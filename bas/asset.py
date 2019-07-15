import asyncio
import datetime
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, TypeVar

from kubernetes import client, watch


class AssetStoreException(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


@dataclass
class Time:
    start_time: Optional[datetime.datetime]
    end_time: Optional[datetime.datetime]


@dataclass
class PackageSource:
    url: str
    filter: str


__group = 'assetstore.kyma-project.io'

__version = 'v1alpha2'

__plural = 'assets'


def create_asset(asset_name: str,
                 bucket_name: str,
                 namespace: str,
                 package_source: PackageSource,
                 api_client: client.api_client,
                 benchmark_uuid: str):
    try:
        client.CustomObjectsApi(api_client).create_namespaced_custom_object(
            async_req=True,
            group=__group,
            version=__version,
            plural=__plural,
            namespace=namespace,
            body=__create_package_asset_body(
                asset_name=asset_name,
                bucket_name=bucket_name,
                namespace=namespace,
                package_source=package_source,
                benchmark_uuid=benchmark_uuid,
            ))
    except KeyboardInterrupt:
        logging.warning(
            f'interrupted asset creation: {bucket_name}/{asset_name} in {namespace}')


def __create_package_asset_body(asset_name: str,
                                bucket_name: str,
                                namespace: str,
                                package_source: PackageSource,
                                benchmark_uuid: str) -> dict:
    return {
        'apiVersion': f'{__group}/{__version}',
        'kind': 'Asset',
        'metadata': {
            'labels': {
                'benchmark': benchmark_uuid,
            },
            'name': asset_name,
            'namespace': namespace,
        },
        'spec': {
            'bucketRef': {
                'name': bucket_name,
            },
            'source': {
                'url': package_source.url,
                'filter': package_source.filter,
                'mode': 'package',
            }
        }
    }


T = TypeVar('T')


def safe_get(d: Dict, default: T, *keys) -> T:
    for key in keys:
        try:
            d = d[key]
        except KeyError:
            return default
    return d


async def watch_assets_create(namespace: str,
                              asset_names: List[str],
                              benchmark_uuid: str) -> datetime.timedelta:
    w = watch.Watch()
    time_map: Dict[str, Time] = {}
    for event in w.stream(client.CustomObjectsApi().list_namespaced_custom_object,
                          pretty='true',
                          group=__group,
                          version=__version,
                          plural=__plural,
                          namespace=namespace,
                          label_selector=f"benchmark={benchmark_uuid}",
                          watch=True):  # type: Dict
        try:
            logging.debug(event)

            event_type: str = safe_get(event, '', 'type')
            if event_type.lower() == 'error':
                error_message = safe_get(event, 'unknown message', 'object', 'message')
                logging.error(f"error: {error_message}")
                return datetime.timedelta.max

            name: str = safe_get(event, '', 'object', 'metadata', 'name')
            is_in_asset_names = name in asset_names

            # save start time for asset
            if is_in_asset_names and name not in time_map and event_type.lower() == 'added':
                now = datetime.datetime.now()
                time_map[name] = Time(now, None)

            phase: str = safe_get(event, '', 'object', 'status', 'phase')
            if phase.lower() == 'failed':
                logging.error(f"asset store exception, benchmark stopped")
                error_message = safe_get(event, 'unknown error', 'object', 'status', 'message')
                raise AssetStoreException(error_message)

            # save stop time for asset
            if is_in_asset_names and phase.lower() == 'ready':
                now = datetime.datetime.now()
                logging.info(f"asset '{name}' was created in: {now - time_map[name].start_time}")
                time_map[name].end_time = now

            all_assets_created = len(time_map) > 0 and all(
                [time_map[name].end_time is not None for name in time_map])

            # check if all assets were created
            if all_assets_created:
                time_start = min([time_map[name].start_time for name in time_map])
                time_end = max([time_map[name].end_time for name in time_map])
                return time_end - time_start

            await asyncio.sleep(0)

        except KeyboardInterrupt:
            logging.warning('watch_assets interrupted')
            return datetime.timedelta.max


def delete_asset(namespace: str, name: str, api_client: client.api_client):
    client.CustomObjectsApi(api_client=api_client).delete_namespaced_custom_object(
        group=__group,
        version=__version,
        namespace=namespace,
        plural=__plural,
        name=name,
        body=client.V1DeleteOptions(api_version=__version))

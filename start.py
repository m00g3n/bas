"""benchmark asset store

Usage:
  start.py --url=<link> --filter=<filter> [options]
  start.py (-h |--help)

Options:
  -h --help                                 show this help message
  --url=<link>                              a link to archive containing markdown assets
  --filter=<filter>                         asset filter for archive.
  --bucket-name=<bucket_name>               the name of the bucket that archive will be stored in [default: test123]
  --namespace=<namespace>                   kubernetes namespace that assets will be created in [default: default]
  --log-level=<log-level>                   the level of logging, one of: INFO,DEBUG,WARNING,ERROR [default: DEBUG]
  --iteration-number=<iteration_number>     the number of iterations of benchmark [default: 1]
  --asset-number=<asset-number>             the number of assets that will be created during each iteration [default: 5]


"""
import asyncio
import csv
import datetime
import logging
import sys
import uuid
from dataclasses import dataclass
from typing import Dict, List

from docopt import docopt
from kubernetes import config, client

from bas import bucket, asset


@dataclass
class Arguments:
    url: str
    filter: str
    bucket_name: str
    namespace: str
    log_lvl: int
    iteration_number: int
    asset_number: int


results: List[Dict] = []


def parse_arguments() -> Arguments:
    __arguments = docopt(__doc__, version='bas 0.1')
    return Arguments(
        url=__arguments.get('--url'),
        filter=__arguments.get('--filter'),
        bucket_name=__arguments.get('--bucket-name'),
        namespace=__arguments.get('--namespace'),
        log_lvl=logging._nameToLevel.get(__arguments.get('--log-level')),
        iteration_number=int(__arguments.get('--iteration-number')),
        asset_number=int(__arguments.get('--asset-number')),
    )


if __name__ == '__main__':

    args = parse_arguments()

    logging.basicConfig(format='%(asctime)s %(message)s', level=args.log_lvl)
    logging.debug('application started')

    config.load_kube_config()
    api_client = client.api_client.ApiClient(pool_threads=1)

    package_src = asset.PackageSource(url=args.url, filter=args.filter)

    # create bucket CRD
    bucket_cfg = bucket.BucketCfg(args.bucket_name, args.namespace)
    bucket.create_bucket(bucket_cfg)

    io_loop = asyncio.get_event_loop()
    for _ in range(0, args.iteration_number):
        benchmark_uuid = f"{uuid.uuid4()}"
        # generate asset names
        asset_names = [f'testassname{uuid.uuid4()}' for _ in range(0, args.asset_number)]
        logging.debug(f"benchmark uuoid: {benchmark_uuid}")
        try:
            # create Asset CRD objects that will used in benchmark
            for asset_name in asset_names:
                asset.create_asset(asset_name,
                                   args.bucket_name,
                                   args.namespace,
                                   package_src, api_client,
                                   benchmark_uuid)

            duration: datetime.timedelta = io_loop.run_until_complete(
                asset.watch_assets_create(args.namespace, asset_names, benchmark_uuid))
            results.append({
                'ass': args.asset_number,
                'dur': duration.total_seconds(),
            })
            logging.info(f'asset processing time: {duration.total_seconds()}')

        except KeyboardInterrupt:
            logging.warning('main loop interrupted')
            break

        finally:
            # delete Asset CRD objects
            for asset_name in asset_names:
                asset.delete_asset('default', asset_name, api_client)

    io_loop.close()

    if len(results) == 0:
        logging.info('no results')
        exit(0)

    logging.debug('persisting data')
    keys = results[0].keys()
    csv.writer(sys.stdout)
    dict_writer = csv.DictWriter(sys.stdout, keys)
    dict_writer.writeheader()
    dict_writer.writerows(results)
    logging.debug('all done')

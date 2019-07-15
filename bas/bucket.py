import logging
from dataclasses import dataclass

from kubernetes import client
from kubernetes.client.rest import ApiException

__plural = "buckets"

__version = "v1alpha2"

__group = "assetstore.kyma-project.io"


@dataclass
class BucketCfg:
    bucket_name: str
    namespace: str


def __create_bucket_body(bucket_name, namespace: str, **kwargs) -> dict:
    return {
        "kind": "Bucket",
        "apiVersion": "assetstore.kyma-project.io/v1alpha2",
        "metadata": {
            "name": bucket_name,
            "namespace": namespace,
        },
        "spec": {
            "region": "us-east-1",
            "policy": "writeonly",
        }
    }


def create_bucket(bucket_cfg: BucketCfg):
    try:
        client.CustomObjectsApi().create_namespaced_custom_object(
            group=__group,
            version=__version,
            namespace=bucket_cfg.namespace,
            plural=__plural,
            body=__create_bucket_body(
                bucket_cfg.bucket_name,
                bucket_cfg.namespace))

    except ApiException as e:
        if e.status == 409:
            msg = f'{bucket_cfg.bucket_name} already exist in {bucket_cfg.namespace}'
            logging.info(msg)

    except KeyboardInterrupt:
        logging.warning('create_bucket interrupted')

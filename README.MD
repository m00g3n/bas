# Asset store benchmark POC 

| Argument        | Default value | Required  |
| ---------------:|:-------------:|:---------:|
|URL|-|yes|
|FILTER|-|yes|
|ITERATION_NUMBER|1|no|
|ASSET_NUMBER|5|no|

## Requirements

- docker
- access to cluster with [kyma](https://kyma-project.io/docs/root/kyma/#installation-installation)

## set kubectl context

Application will use current kubernetes context.
- To check what context is set invoke: `kubectl config current-context`.
- To find all available contexts invoke: `kubectl config get-contexts`
- To change context invoke `kubectl config use-context <context-name-here>`


## build and run container

- build container
```bash
docker build -t 'bas' .
```

- run benchmark from container
```bash
docker run -t --rm \
    -v ~/.kube/config:/app/config \
    -e URL="https://github.com/kyma-project/kyma/archive/0.8.1.zip" \
    -e FILTER="/docs/kyma/docs/" \
    -e ITERATION_NUMBER=2 \
    -e ASSET_NUMBER=7 \
    bas
```

- run benchmark from container (minikube)
```bash
docker run -t --rm --network host \
        -v ~/.minikube/ca.crt:/app/ca.crt:ro \
        -v ~/.minikube/client.crt:/app/client.crt:ro \
        -v ~/.minikube/client.key:/app/client.key:ro \
        -e MINIKUBE_IP=$(minikube ip) \
        -e URL="https://github.com/kyma-project/kyma/archive/0.8.1.zip" \
        -e FILTER="/docs/kyma/docs/" \
        -e ITERATION_NUMBER=1 \
        -e ASSET_NUMBER=3 \
        bas
```
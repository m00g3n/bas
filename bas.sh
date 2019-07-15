#!/bin/sh

ITERATION_NUMBER=${ITERATION_NUMBER:-5}
ASSET_NUMBER=${ASSET_NUMBER:-10}

sed -i 's/__MINIKUBE__/'"$MINIKUBE_IP"'/g' ./config

python start.py --url=${URL} --filter=${FILTER} \
    --iteration-number=${ITERATION_NUMBER} \
    --asset-number=${ASSET_NUMBER}
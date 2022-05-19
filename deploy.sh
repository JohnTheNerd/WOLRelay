#!/bin/bash

set -ex

if [ -z "$1" ]; then
  echo "Please provide the image tag as the only argument!"
  exit 1
fi

docker run --rm --privileged multiarch/qemu-user-static --reset -p yes

docker login
docker buildx create --platform linux/amd64,linux/arm64,linux/armhf --name wolrelay --use || docker buildx use wolrelay
docker buildx build -t "$1" --platform linux/amd64,linux/arm64,linux/armhf --push .
docker logout

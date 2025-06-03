#!/bin/bash
export DOCKER_BUILDKIT=1 
export tag=$(jq -r '.version' web/package.json)
# docker context create arm_node --docker "host=tcp://127.0.0.1:8375"
# docker buildx create --use --name build --platform linux/amd64 default
# docker buildx create --append --name build --platform linux/arm64 arm_node
# ssh -l opc -L 8375:*:2375 -L 27018:*:27017 tooka.com.br

docker buildx build --platform linux/arm64,linux/amd64 . -t liberatti/nproxy:latest -t "liberatti/nproxy:$tag" --push
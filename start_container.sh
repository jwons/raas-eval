#!/bin/bash

docker run \
  -e JUPYTER_ENABLE_LAB=yes \
  -p 8888:8888 \
  --name raas-eval \
  --mount type=bind,source="$(pwd)",target=/home/jovyan/work \
  jupyter/scipy-notebook


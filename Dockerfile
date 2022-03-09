FROM jupyter/scipy-notebook:4d9c9bd9ced0

COPY . /home/jovyan/work

USER root

RUN sudo chown -R jovyan:users /home/jovyan/work
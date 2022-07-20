FROM python:3.8-slim

RUN apt-get update && apt-get install -y curl

COPY . /rancher-gitlab-deploy/

WORKDIR /rancher-gitlab-deploy
RUN python /rancher-gitlab-deploy/setup.py install
RUN ln -s /usr/local/bin/rancher-gitlab-deploy /usr/local/bin/upgrade


CMD rancher-gitlab-deploy
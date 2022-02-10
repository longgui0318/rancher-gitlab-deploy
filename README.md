# Rancher GitLab Deployment Tool

对 cdrx/rancher-gitlab-deploy 项目的修改版，去除了很多功能，支持rancher2.6

## Usage

You will need to create a set of API keys in Rancher and save them as secret variables in GitLab for your project.

Three secret variables are required:

`RANCHER_URL` (eg `https://rancher.example.com`)

`RANCHER_ACCESS_KEY`

`RANCHER_SECRET_KEY`

For example, in your `gitlab-ci.yml`:

```
deploy:
  stage: deploy
  image: longgui0318/rancher-gitlab-deploy
  script:
    - upgrade --cluster your-cluster --namespace your-group  --service your-service --new-image your-new-image
```

## GitLab CI Example

Complete gitlab-ci.yml:

```
image: docker:latest
services:
  - docker:dind

stages:
  - build
  - deploy

build:
  stage: build
  script:
    - docker login -u gitlab-ci-token -p $CI_BUILD_TOKEN registry.example.com
    - docker build -t registry.example.com/group/project .
    - docker push registry.example.com/group/project

deploy:
  stage: deploy
  image: longgui0318/rancher-gitlab-deploy
  script:
    - upgrade --cluster your-cluster --namespace your-group  --service your-service --new-image your-new-image
```

## Help

```
$ rancher-gitlab-deploy --help

Usage: rancher-gitlab-deploy [OPTIONS]

  Performs an in service upgrade of the service specified on the command
  line

Options:
  --rancher-url TEXT              The URL for your Rancher server, eg:
                                  http://rancher:8000  [required]
  --rancher-key TEXT              The key for the access API key
                                  [required]
  --rancher-secret TEXT           The secret for the access API key
                                  [required]
  --cluster TEXT                  The cluster name in Rancher
                                  [required]
  --namespace TEXT                The namespace name in Rancher
                                  [required]
  --service TEXT                  The service name in Rancher
                                  [required]
  --new-image TEXT                If specified, replace the image (and :tag)
                                  with this one during the upgrade
                                  [required]
  --debug / --no-debug            Enable HTTP Debugging
  --help                          Show this message and exit.
```

## License

MIT

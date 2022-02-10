#!/usr/bin/env python
import logging
import sys
import json

import click
import requests
from requests import HTTPError

try:
    from httplib import HTTPConnection  # py2
except ImportError:
    from http.client import HTTPConnection  # py3

@click.command()
@click.option(
    "--rancher-url",
    envvar="RANCHER_URL",
    required=True,
    help="The URL for your Rancher server, eg: http://rancher:8000",
)
@click.option(
    "--rancher-key",
    envvar="RANCHER_ACCESS_KEY",
    required=True,
    help="The key for the access API key",
)
@click.option(
    "--rancher-secret",
    envvar="RANCHER_SECRET_KEY",
    required=True,
    help="The secret for the access API key",
)
@click.option(
    "--cluster",
    envvar="RANCHER_APP_CLUSTER",
    required=True,
    help="The cluster name in Rancher",
)
@click.option(
    "--namespace",
    envvar="RANCHER_APP_NAMESPACE",
    required=True,
    help="The namespace name in Rancher",
)
@click.option(
    "--service",
    envvar="RANCHER_APP_SERVICE",
    required=True,
    help="The service name in Rancher",
)
@click.option(
    "--new-image",
    required=True,
    help="If specified, replace the image (and :tag) with this one during the upgrade",
)
@click.option(
    "--debug/--no-debug",
    default=False,
    help="Enable HTTP Debugging",
)
def main(
    rancher_url,
    rancher_key,
    rancher_secret,
    cluster,
    namespace,
    service,
    new_image,
    debug,
):
    """Performs an in service upgrade of the service specified on the command line"""
    if debug:
        debug_requests_on()

    # split url to protocol and host
    if "://" not in rancher_url:
        bail("Rancher URL 配置不正确")

    protocol, host = rancher_url.split("://")
    api = "%s://%s/v3" % (protocol, host)
    api_k8s = "%s://%s/k8s/clusters" % (protocol, host)

    namespace = namespace.replace(".", "-")
    service = service.replace(".", "-")

    session = requests.Session()

    # 0 -> 配置认证信息
    session.auth = (rancher_key, rancher_secret)

    # 1 -> 查找集群id
    try:
        r = session.get("%s/clusters" % api)
        r.raise_for_status()
    except HTTPError:
        bail("接口请求失败,请确认地址及api key配置正确与否?")
    else:
        clusters = r.json()["data"]
    cluster_id = None
    for c in clusters:
        if c["name"].lower()== cluster.lower():
            cluster_id = c["id"]
            break
    if cluster_id is None:
        bail("没有找到名称为['%s']的集群" % cluster)

    msg("集群定位成功,查找服务中......")

    # 2 -> 查找服务的操作地址
    try:
        r = session.get("%s/%s/v1/apps.deployments" % (api_k8s, cluster_id))
        r.raise_for_status()
    except HTTPError:
        bail("['%s']集群服务列表获取失败!" % cluster)
    else:
        services = r.json()["data"]
    service_id = "%s/%s" % (namespace, service)
    service_links = None
    for s in services:
        if s["id"].lower() == service_id.lower():
            service_links = s["links"]
            break
    if service_links is None:
        bail("集群['%s']中没有找到名称为['%s']的服务" % (cluster,service_id))
    
    msg("服务定位成功,正在更新配置......")

    # 3 -> 获取并更新配置
    service_config = None
    try:
        r = session.get(service_links["view"])
        r.raise_for_status()
    except HTTPError:
        bail("获取['%s']配置失败!" % service_id)
    else:
        service_config = r.json()
    if service_config is None:
        bail("获取的['%s']配置为空!" % service_id)
    if service_config["spec"] is None:
        bail("获取的['%s']配置.spec为空!" % service_id)
    if service_config["spec"]["template"] is None:
        bail("获取的['%s']配置.spec.template为空!" % service_id)
    if service_config["spec"]["template"]["spec"] is None:
        bail("获取的['%s']配置.spec.template.spec为空!" % service_id)
    if service_config["spec"]["template"]["spec"]["containers"] is None:
        bail("获取的['%s']配置.spec.template.spec.containers为空!" % service_id)
    if len(service_config["spec"]["template"]["spec"]["containers"]) != 1:
        bail("获取的['%s']配置.spec.template.spec.containers 数量不为1,不允许更新此类不明确容器!" % service_id)
    if  service_config["spec"]["template"]["spec"]["containers"][0] is None:
        bail("获取的['%s']配置.spec.template.spec.containers[0]为空!" % service_id)
    service_config["spec"]["template"]["spec"]["containers"][0]["image"] = new_image
    try:
        r = session.put(service_links["update"],json.dumps(service_config))
        r.raise_for_status()
    except HTTPError:
        bail("更新['%s']配置失败!" % service_id)

    msg("配置更新成功,服务升级中......")
    msg("请前往%s查看是否成功!" % rancher_url)
    
    sys.exit(0)


def msg(message):
    click.echo(click.style(message, fg="green"))


def warn(message):
    click.echo(click.style(message, fg="yellow"))


def bail(message, exit=True):
    click.echo(click.style("Error: " + message, fg="red"))
    if exit:
        sys.exit(1)


def debug_requests_on():
    """Switches on logging of the requests module."""
    HTTPConnection.debuglevel = 1

    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
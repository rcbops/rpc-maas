#!/usr/bin/env python3
import os
import sys

import click
from rackspace_monitoring.providers import get_driver
from rackspace_monitoring.types import Provider
import requests


@click.group()
@click.option("--username", required=True)
@click.option("--api-key", required=True)
@click.pass_context
def cli(ctx, api_key, username):
    ctx.obj = {
        'username': username,
        'api-key': api_key
    }
    url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
    headers = {"Content-type": "application/json"}
    data = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": api_key
            }
        }
    }

    try:
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(e)
        sys.exit(1)
    except requests.exceptions.HTTPError as httpe:
        print(httpe)
        sys.exit(1)
    resp = r.json()
    ctx.obj['token'] = resp['access']['token']['id']
    monitoring_service = next(
        s for s in resp['access']['serviceCatalog']
        if s["name"] == "cloudMonitoring"
    )
    ctx.obj['url'] = monitoring_service['endpoints'][0]['publicURL']


@click.command(name='get_token_url')
@click.pass_context
def get_token_url(ctx):
    cred_file = os.path.expanduser('~/maas-vars.rc')
    with open(cred_file, 'w') as f:
        f.write(
            "export MAAS_AUTH_TOKEN={token}\n"
            "export MAAS_API_URL={url}\n".format(
                token=ctx.obj['token'],
                url=ctx.obj['url']
            )
        )

    click.echo(
        'Credentials file written to "{cred_file}"'.format(
            cred_file=cred_file
        )
    )
    return ctx.obj['token'], ctx.obj['url']


@click.command(name='set_webhook_token')
@click.option("--token", 'webhook_token', required=True)
@click.pass_context
def set_webhook_token(ctx, webhook_token):
    """Sets the token that is included in MaaS webhook notifications

    This is one method of verifying that receieved requests are
    from MaaS. This is per account.
    """
    auth_token, url = ctx.invoke(get_token_url)
    try:
        response = requests.put(
            "{url}/account".format(url=url),
            headers={'X-Auth-Token': auth_token},
            json={'webhook_token': webhook_token})
        response.raise_for_status()
        click.echo("Webhook token set to {}".format(webhook_token))
    except requests.exceptions.HTTPError as e:
        click.echo(response.text)
        raise e


@click.command(name='get_entity_id')
@click.option("--label", help="label of entity to get ID for", required=True)
@click.pass_context
def get_entity_id(ctx, label):
    Cls = get_driver(Provider.RACKSPACE)
    driver = Cls(ctx.obj['username'], ctx.obj['api-key'])
    entities = driver.list_entities()
    for e in entities:
        if label == e.label:
            click.echo(e.id)


cli.add_command(get_token_url)
cli.add_command(set_webhook_token)
cli.add_command(get_entity_id)


if __name__ == "__main__":
    cli()

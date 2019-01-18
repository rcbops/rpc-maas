#!/usr/bin/env python
import argparse
import json
import os
import sys

import requests


# Query public identity with a username and apikey
def auth(username, apikey):
    url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
    headers = {"Content-type": "application/json"}
    data = {
        "auth": {
            "RAX-KSKEY:apiKeyCredentials": {
                "username": username,
                "apiKey": apikey
            }
        }
    }

    try:
        r = requests.post(url, headers=headers, json=data)
        r.raise_for_status()
    except requests.exceptions.RequestException as e:
        print e
        sys.exit(1)
    except requests.exceptions.HTTPError as httpe:
        print httpe
        sys.exit(1)
    return r.json()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Obtain maas_api_url and'
                                     'maas_auth_token from a username and'
                                     'apikey')
    parser.add_argument('--username', type=str, help='RAX cloud username')
    parser.add_argument('--apikey', type=str, help='RAX cloud apikey')
    args = parser.parse_args()

    resp = auth(args.username, args.apikey)
    token = resp['access']['token']['id']
    for service in resp['access']['serviceCatalog']:
        if service['name'] == 'cloudMonitoring':
            url = service['endpoints'][0]['publicURL']

    cred_file = os.path.expanduser('~/maas-vars.rc')
    with open(cred_file, 'w') as f:
        f.write(
            "export MAAS_AUTH_TOKEN={token}\n"
            "export MAAS_API_URL={url}\n".format(
                token=token,
                url=url
            )
        )
    print('Credentials file written to "%s"') % cred_file

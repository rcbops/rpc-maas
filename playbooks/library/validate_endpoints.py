#!/usr/bin/env python
# Copyright 2019, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from urlparse import urlparse

from ansible.module_utils.basic import *  # noqa: ignore=H303
import requests


DOCUMENTATION = """
---
module: validate_endpoints
short_description:
    - Module to obtain a proper keystone v3 endpoint for clouds.yaml.
description:
    - This module takes a list containing a CSV dump of keystone endpoints.
      It iterates through to ensure that a v3 endpoint exists. If one does not
      exist, it will fail because MaaS is incompatible with v2.0 endpoints.
options:
    endpoints:
        description:
            - A list of endpoint data reported by the openstack client.
        required: true
author:
    - Nathan Pawelek (@npawelek)
"""

EXAMPLES = """
- validate_endpoints:
    endpoints: [
        "be0a31e4bc694d35ad4a5ec23d05ade5,RegionOne,keystone,identity,True,internal,http://172.29.236.100:5000",
        "e55f530e90b44a28bbd2d45c4fee8704,RegionOne,keystone,identity,True,public,https://104.239.157.32:5000",
        "f944a2864deb4f6f99a1c39043ef3199,RegionOne,keystone,identity,True,admin,http://172.29.236.100:5000"
    ]
"""


def parse_endpoints(sess, endpoints):

    info = dict()

    # Prioritize admin and internal interfaces only
    for interface in 'admin', 'internal':
        for endpoint in endpoints:
            if interface in endpoint:

                # Parse the URL and strip off the path to ensure all endpoint
                # versions are discovered
                # https://wiki.openstack.org/wiki/VersionDiscovery
                parsed = urlparse(endpoint.split(',')[-1])
                url = parsed.geturl().strip(parsed.path)

                r = sess.get(url)
                if r.status_code == 300:
                    versions = r.json()['versions']['values']
                    for version in versions:
                        for link in version['links']:
                            if '/v3' in link['href']:
                                info['auth_url'] = str(link['href'])
                                info['interface'] = interface
                                info['region'] = endpoint.split(',')[1]
                                return info
    else:
        return info


def main():
    module = AnsibleModule(
        argument_spec=dict(
            endpoints=dict(
                required=True,
                type=list
            )
        ),
        supports_check_mode=False
    )

    endpoints = module.params.get('endpoints')
    s = requests.Session()
    s.headers.update({'Content-Type': 'application/json'})

    results = parse_endpoints(s, endpoints)

    if len(results) > 0:
        module.exit_json(
            changed=False,
            ansible_facts={
                'auth_url': results['auth_url'].rstrip('/'),
                'interface': results['interface'],
                'region': results['region']
            }
        )
    else:
        message = "Unable to detect valid keystone v3 endpoint."
        module.fail_json(msg=message)


if __name__ == '__main__':
    main()

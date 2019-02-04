#!/usr/bin/env python

# Copyright 2017, Rackspace US, Inc.
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

import argparse

from maas_common import get_auth_ref
from maas_common import get_keystone_client
from maas_common import get_nova_client
from maas_common import get_os_component_major_api_version
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    auth_token = keystone.auth_token
    tenant_id = keystone.tenant_id
    nova_version = '.'.join(
        map(str, get_os_component_major_api_version('nova')))

    compute_endpoint = (
        '{protocol}://{hostname}:{port}/v{version}/{tenant_id}'.format(
            hostname=args.hostname,
            tenant_id=tenant_id,
            protocol=args.protocol,
            port=args.port,
            version=nova_version
        )
    )
    try:
        nova = get_nova_client(auth_token=auth_token,
                               bypass_url=compute_endpoint)

    # not gathering api status metric here so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_nova')
        status_err(str(e), m_name='maas_nova')
    else:
        metric_bool('client_success', True, m_name='maas_nova')

    # gather nova service states
    if args.host:
        services = nova.services.list(host=args.host)
    else:
        services = nova.services.list()

    if len(services) == 0:
        status_err("No host(s) found in the service list", m_name='maas_nova')

    # return all the things
    status_ok(m_name='maas_nova')
    for service in services:
        service_is_up = True

        if service.status == 'enabled' and service.state == 'down':
            service_is_up = False

        if args.host:
            name = '%s_status' % service.binary
        else:
            name = '%s_on_host_%s_status' % (service.binary, service.host)

        # replace the first 'nova' so the metric name would be like:
        # 'ironic-compute_status'
        # notice 'ironic-conductor' is different than 'nova-conductor'
        # on ironic-compute box, so we preserve nova-conductor metric
        if 'conductor' not in name:
            name = name.replace('nova', 'ironic', 1)

        metric_bool(name, service_is_up, m_name='maas_nova')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check nova services')
    parser.add_argument('hostname',
                        type=str,
                        help='Nova API hostname or IP address')
    parser.add_argument('--host',
                        type=str,
                        help='Only return metrics for specified host',
                        default=None)
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for the nova API')
    parser.add_argument('--port',
                        action='store',
                        default='8774',
                        help='Port the nova API service is running on.')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

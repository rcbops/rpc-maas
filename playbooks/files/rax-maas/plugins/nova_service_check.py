#!/usr/bin/env python

# Copyright 2014, Rackspace US, Inc.
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
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_err_no_exit
from maas_common import status_ok
from maas_common import NOVA_SERVICE_TYPE_LIST


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    auth_token = keystone.auth_token
    tenant_id = keystone.tenant_id
    nova_version = '.'.join(
        map(str, get_os_component_major_api_version('nova')))

    COMPUTE_ENDPOINT = (
        '{protocol}://{hostname}:8774/v{version}/{tenant_id}'
        .format(protocol=args.protocol, hostname=args.hostname,
                version=nova_version, tenant_id=tenant_id)
    )
    try:
        nova = get_nova_client(auth_token=auth_token,
                               bypass_url=COMPUTE_ENDPOINT)

    # not gathering api status metric here so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_nova')
        for nova_service_type in NOVA_SERVICE_TYPE_LIST:
            metric('%s_status' % nova_service_type,
                   'string',
                   '%s cannot reach API' % nova_service_type,
                   m_name='maas_nova')
        status_err_no_exit(str(e), m_name='maas_nova')
        return
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
        service_is_up = "Yes"

        if service.status.lower() == 'enabled':
            if service.state.lower() == 'down':
                service_is_up = "No"
        elif service.status.lower() == 'disabled':
            if service.disabled_reason:
                if 'auto' in service.disabled_reason.lower():
                    service_is_up = "No"

        if args.host:
            name = '%s_status' % service.binary
        else:
            name = '%s_on_host_%s_status' % (service.binary, service.host)

        metric(name, 'string', service_is_up, m_name='maas_nova')


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
                        type=str,
                        help='Protocol to use for contacting nova',
                        default='http')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

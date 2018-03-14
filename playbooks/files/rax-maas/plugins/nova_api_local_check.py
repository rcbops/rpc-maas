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
import collections
import time

import ipaddr
from maas_common import get_auth_ref
from maas_common import get_keystone_client
from maas_common import get_nova_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from novaclient.client import exceptions as exc

SERVER_STATUSES = ['ACTIVE', 'STOPPED', 'ERROR']


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    tenant_id = keystone.tenant_id

    compute_endpoint = (
        '{protocol}://{ip}:{port}/v2.1/{tenant_id}'.format(
            ip=args.ip,
            tenant_id=tenant_id,
            protocol=args.protocol,
            port=args.port
        )
    )

    try:
        if args.ip:
            nova = get_nova_client(bypass_url=compute_endpoint)
        else:
            nova = get_nova_client()

        is_up = True
    except exc.ClientException:
        is_up = False
        metric_bool('client_success', False, m_name='maas_nova')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_nova')
        status_err(str(e), m_name='maas_nova')
    else:
        metric_bool('client_success', True, m_name='maas_nova')
        # time something arbitrary
        start = time.time()
        nova.services.list()
        end = time.time()
        milliseconds = (end - start) * 1000

        servers = nova.servers.list(search_opts={'all_tenants': 1})
        # gather some metrics
        status_count = collections.Counter([s.status for s in servers])

    status_ok(m_name='maas_nova')
    metric_bool('nova_api_local_status', is_up, m_name='maas_nova')
    # only want to send other metrics if api is up
    if is_up:
        metric('nova_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')
        for status in SERVER_STATUSES:
            metric('nova_instances_in_state_%s' % status,
                   'uint32',
                   status_count[status], 'instances')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Nova API against local or remote address')
    parser.add_argument('ip', nargs='?',
                        type=ipaddr.IPv4Address,
                        help='Optional Nova API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='8774',
                        help='Port for the nova API service')
    parser.add_argument('--protocol',
                        default='http',
                        help='Protocol used to contact the nova API service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

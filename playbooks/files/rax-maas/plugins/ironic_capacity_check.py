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

import ipaddr
from ironicclient import exc
from maas_common import get_auth_ref
from maas_common import get_ironic_client
from maas_common import get_os_component_major_api_version
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(auth_ref, args):
    ironic_version = get_os_component_major_api_version('ironic')[0]
    ironic_endpoint = ('{protocol}://{ip}:{port}/v{version}'.format(
        ip=args.ip,
        protocol=args.protocol,
        port=args.port,
        version=ironic_version
    ))

    try:
        if args.ip:
            ironic = get_ironic_client(endpoint=ironic_endpoint)
        else:
            ironic = get_ironic_client()

        is_up = True

    except exc.ClientException:
        is_up = False
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_ironic')
        status_err(str(e), m_name='maas_ironic')
        return
    else:
        metric_bool('client_success', True, m_name='maas_ironic')
        # pass limit=0 to list all nodes list without pagination
        all_nodes = ironic.node.list(limit=0)
        status_ok(m_name='maas_ironic')

    if is_up:
        maint_nodes = [node for node in all_nodes if node.maintenance]
        maint_nodes_count = len(maint_nodes)
        total_nodes = len(all_nodes)
        up_nodes = total_nodes - maint_nodes_count
        metric('ironic_up_nodes_count', 'uint32', up_nodes)
        metric('ironic_total_nodes_count', 'uint32', total_nodes)


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Ironic capacity against local or remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Ironic capacity against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol used to connect to ironic API')
    parser.add_argument('--port',
                        action='store',
                        default='6385',
                        help='Port for ironic API')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

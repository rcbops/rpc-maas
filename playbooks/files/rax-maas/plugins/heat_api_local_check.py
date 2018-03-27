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
import time

from heatclient import exc
import ipaddr
from maas_common import get_auth_ref
from maas_common import get_heat_client
from maas_common import get_keystone_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    tenant_id = keystone.tenant_id

    heat_endpoint = ('{protocol}://{ip}:{port}/v1/{tenant}'.format(
        ip=args.ip,
        tenant=tenant_id,
        protocol=args.protocol,
        port=args.port
    ))

    try:
        if args.ip:
            heat = get_heat_client(endpoint=heat_endpoint)
        else:
            heat = get_heat_client()

        is_up = True
    except exc.HTTPException as e:
        is_up = False
        metric_bool('client_success', False, m_name='maas_heat')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_heat')
        status_err(str(e), m_name='maas_heat')
    else:
        metric_bool('client_success', True, m_name='maas_heat')
        # time something arbitrary
        start = time.time()
        heat.build_info.build_info()
        end = time.time()
        milliseconds = (end - start) * 1000

    status_ok(m_name='maas_heat')
    metric_bool('heat_api_local_status', is_up, m_name='maas_heat')
    if is_up:
        # only want to send other metrics if api is up
        metric('heat_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Heat API against local or remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Heat API against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        action='store',
                        default='8004',
                        help='Port to use for the local heat API')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol for the local heat API')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

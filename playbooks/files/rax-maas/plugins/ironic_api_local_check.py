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
import time

import ipaddr
from ironicclient import exc
from maas_common import get_auth_ref
from maas_common import get_ironic_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(auth_ref, args):

    IRONIC_ENDPOINT = ('http://{ip}:6385/v1'.format(ip=args.ip))

    try:
        if args.ip:
            ironic = get_ironic_client(endpoint=IRONIC_ENDPOINT)
        else:
            ironic = get_ironic_client()

        is_up = True

    except exc.ClientException:
        is_up = False
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_ironic')
        status_err(str(e), m_name='maas_ironic')
    else:
        metric_bool('client_success', True, m_name='maas_ironic')
        # time something arbitrary
        start = time.time()
        ironic.node.list()
        end = time.time()
        milliseconds = (end - start) * 1000

    status_ok(m_name='maas_ironic')
    metric_bool('ironic_api_local_status', is_up, m_name='maas_ironic')
    if is_up:
        # only want to send other metrics if api is up
        metric('ironic_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Ironic API against local or remote address')
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Ironic API against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

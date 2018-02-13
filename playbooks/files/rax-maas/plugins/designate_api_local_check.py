#!/usr/bin/env python

# Copyright 2018, Rackspace US, Inc.
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
import datetime

import ipaddr
from maas_common import get_auth_ref
from maas_common import get_endpoint_url_for_service
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests


def check(auth_ref, args):
    DESIGNATE_ENDPOINT = '{protocol}://{ip}:9001/'.format(
        protocol=args.protocol, ip=args.ip)

    try:
        if args.ip:
            endpoint = DESIGNATE_ENDPOINT
        else:
            endpoint = get_endpoint_url_for_service(
                'dns', auth_ref, 'internal')
        # time something arbitrary
        start = datetime.datetime.now()
        r = requests.get(endpoint)
        end = datetime.datetime.now()
        api_is_up = (r.status_code == 200)
    except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
        api_is_up = False
        metric_bool('client_success', False, m_name='maas_designate')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_designate')
        status_err(str(e), m_name='maas_designate')
    else:
        metric_bool('client_success', True, m_name='maas_designate')
        dt = (end - start)
        milliseconds = (dt.microseconds + dt.seconds * 10 ** 6) / 10 ** 3

    status_ok(m_name='maas_designate')
    metric_bool('designate_api_local_status',
                api_is_up, m_name='maas_designate')
    if api_is_up:
        # only want to send other metrics if api is up
        metric('designate_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Designate API against local or remote address')
    parser.add_argument('protocol', nargs='?',
                        help="Protocol for check (http or https)")
    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Designate API against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

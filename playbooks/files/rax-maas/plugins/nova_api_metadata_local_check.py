#!/usr/bin/env python3

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

import ipaddr
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests
from requests import exceptions as exc


def check(args):
    metadata_endpoint = ('{protocol}://{ip}:{port}'.format(
        ip=args.ip,
        protocol=args.protocol,
        port=args.port
    ))
    is_up = True

    s = requests.Session()

    try:
        # looks like we can only get / (ec2 versions) without specifying
        # an instance ID and other headers
        versions = s.get('%s/' % metadata_endpoint,
                         verify=False,
                         timeout=180)
        milliseconds = versions.elapsed.total_seconds() * 1000
        if not versions.ok or '1.0' not in versions.content.decode().splitlines():
            is_up = False
    except (exc.ConnectionError, exc.HTTPError, exc.Timeout) as e:
        is_up = False
        metric_bool('client_success', False, m_name='maas_nova')
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_nova')
        status_err(str(e), m_name='maas_nova')
    else:
        metric_bool('client_success', True, m_name='maas_nova')

    status_ok(m_name='maas_nova')
    metric_bool('nova_api_metadata_local_status', is_up, m_name='maas_nova')
    # only want to send other metrics if api is up
    if is_up:
        metric('nova_api_metadata_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check nova-api-metdata API')
    parser.add_argument('ip',
                        type=ipaddr.IPv4Address,
                        help='nova-api-metadata IP address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        default='8775',
                        help='Port for the nova metadata service')
    parser.add_argument('--protocol',
                        default='http',
                        help='Protocol for the nova metadata service')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

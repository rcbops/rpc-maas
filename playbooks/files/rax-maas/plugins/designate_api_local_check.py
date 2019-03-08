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

import ipaddr
from maas_common import generate_local_endpoint
from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc


def check(args):
    designate = get_openstack_client('dns')

    try:
        if args.ip:
            # Arbitrary call to /zones to ensure the local API is up
            designate_local_endpoint = generate_local_endpoint(
                str(designate.get_endpoint()), args.ip, args.port,
                args.protocol, '/zones'
            )
            resp = designate.session.get(designate_local_endpoint, timeout=180)
            milliseconds = resp.elapsed.total_seconds() * 1000
        # NOTE(npawelek): At the time of converting to OpenStack SDK,
        # DNS is not yet fully integrated. Excluding integration with
        # the client directly until a later time.

        api_is_up = resp.ok
    except (exc.HTTPError, exc.Timeout, exc.ConnectionError):
        api_is_up = False
        metric_bool('client_success', False, m_name='maas_designate')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_designate')
        status_err(str(e), m_name='maas_designate')
    else:
        metric_bool('client_success', True, m_name='maas_designate')

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
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Designate API against local or remote address')

    parser.add_argument('ip', nargs='?', type=ipaddr.IPv4Address,
                        help="Check Designate API against "
                        " local or remote address")
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help="Protocol to run the check against")
    parser.add_argument('--port',
                        default="9001",
                        help="Port the Designate service is running on.")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

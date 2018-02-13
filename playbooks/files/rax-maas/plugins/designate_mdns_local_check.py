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

import dns.message
import dns.query
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(args):
    try:
        # attempt a query to example.com
        # return good check on any valid response
        start = datetime.datetime.now()
        message = dns.message.make_query("example.org", "A")
        answer = dns.query.udp(message, timeout=5, where=args.ip, port=5354)
        end = datetime.datetime.now()
        # int of return code
        mdns_is_up = (answer.rcode() <= 16)
    except (dns.exception.Timeout):
        mdns_is_up = False
        metric_bool('client_success', False, m_name='maas_designate')
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_designate')
        status_err(str(e), m_name='maas_designate')
    else:
        metric_bool('client_success', True, m_name='maas_designate')
        dt = (end - start)
        milliseconds = (dt.microseconds + dt.seconds * 10 ** 6) / 10 ** 3

    status_ok(m_name='maas_designate')
    metric_bool('designate_mdns_local_status',
                mdns_is_up, m_name='maas_designate')
    if mdns_is_up:
        # only want to send other metrics if api is up
        metric('designate_mdns_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Designate MDNS against local or remote address')
    parser.add_argument('ip', nargs='?',
                        help="Check Designate mdns service against "
                        " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

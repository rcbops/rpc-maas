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
import datetime

import subprocess
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok

RACKSPACE_SYSTEM_NS = "rackspace-system"


def check(args):
    try:
        start = datetime.datetime.now()
        # this is lame but the k8 python client did not work
        ret = subprocess.check_output(
            ['kubectl', "--kubeconfig=%s" % args.kubeconfig,
             "--namespace=%s" % RACKSPACE_SYSTEM_NS, 'get', 'pods'])
        end = datetime.datetime.now()
        api_is_up = (len(ret.split(
            '\n')) > 1)  # if rack system is empty something is terribly wrong
    except subprocess.CalledProcessError as e:
        api_is_up = False
        metric_bool('client_success', False, m_name='maas_managed_k8')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_managed_k8')
        status_err(str(e), m_name='maas_managed_k8')
    else:
        metric_bool('client_success', True, m_name='maas_managed_k8')
        dt = (end - start)
        milliseconds = (dt.microseconds + dt.seconds * 10 ** 6) / 10 ** 3

    status_ok(m_name='maas_managed_k8')
    metric_bool('managed_k8_api_local_status', api_is_up,
                m_name='maas_managed_k8')
    if api_is_up:
        # only want to send other metrics if api is up
        metric('managed_k8_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check K8 Cluster API against local or remote address')
    parser.add_argument('--kubeconfig', nargs='?', required=True,
                        help="Kube Config file to use")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

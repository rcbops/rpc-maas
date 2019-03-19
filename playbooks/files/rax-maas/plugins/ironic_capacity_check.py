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

from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def check(args):
    ironic = get_openstack_client('baremetal')

    try:
        nodes = [i for i in ironic.nodes()]

    except Exception as e:
        metric_bool('client_success', False, m_name='maas_ironic')
        status_err(str(e), m_name='maas_ironic')
    else:
        is_up = True
        metric_bool('client_success', True, m_name='maas_ironic')
        status_ok(m_name='maas_ironic')

    if is_up:
        maint_nodes = [n for n in nodes if n.is_maintenance]
        maint_nodes_count = len(maint_nodes)
        total_nodes = len(nodes)
        up_nodes = total_nodes - maint_nodes_count
        metric('ironic_up_nodes_count', 'uint32', up_nodes)
        metric('ironic_total_nodes_count', 'uint32', total_nodes)


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Ironic capacity from baremetal API')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

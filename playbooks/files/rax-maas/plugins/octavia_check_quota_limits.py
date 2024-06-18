#!/usr/bin/env python3

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
from __future__ import division

import argparse

from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc


def check(args):
    nova = get_openstack_client('compute')

    try:
        if args.tenant_id:
            params = {'tenant_id': args.tenant_id,
                      'project_id': args.tenant_id}
        else:
            params = {}

        compute_url = '%s/limits' % str(nova.get_endpoint())
        compute_resp = nova.session.get(compute_url, params=params,
                                        timeout=180)

        if compute_resp.status_code != 200:
            raise Exception("Nova returned status code %s" % str(
                compute_resp.status_code))
        nova_limits = compute_resp.json()['limits']['absolute']

        metric_bool('client_success', True, m_name='maas_octavia')
        status_ok(m_name='maas_octavia')
        metric('octavia_cores_quota_usage',
               'double',
               '%.3f' % (
                   max(0, nova_limits['totalCoresUsed'] / nova_limits[
                       'maxTotalCores'] * 100)),
               '%')
        metric('octavia_instances_quota_usage',
               'double',
               '%.3f' % (max(0, nova_limits['totalInstancesUsed'] /
                             nova_limits['maxTotalInstances'] * 100)),
               '%')
        metric('octavia_ram_quota_usage',
               'double',
               '%.3f' % (
                   max(0, nova_limits['totalRAMUsed'] / nova_limits[
                       'maxTotalRAMSize'] * 100)),
               '%')
        metric('octavia_server_group_quota_usage',
               'double',
               '%.3f' % (max(0, nova_limits['totalServerGroupsUsed'] /
                             nova_limits['maxServerGroups'] * 100)),
               '%')

        # Neutron got it's limit support in Pike...

    except (exc.HTTPError, exc.Timeout, exc.ConnectionError):
        metric_bool('client_success', False, m_name='maas_octavia')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_octavia')
        status_err(str(e), m_name='maas_octavia')
    else:
        metric_bool('client_success', True, m_name='maas_octavia')

    status_ok(m_name='maas_octavia')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Octavia API against local or remote address')
    parser.add_argument('tenant_id', nargs='?',
                        help="Check Octavia API against "
                             " local or remote address")
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

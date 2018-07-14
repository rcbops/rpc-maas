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
from __future__ import division

import argparse

from maas_common import get_auth_ref
from maas_common import get_endpoint_url_for_service
from maas_common import get_keystone_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    auth_token = keystone.auth_token

    s = requests.Session()

    s.headers.update(
        {'Content-type': 'application/json',
         'x-auth-token': auth_token})
    try:
        if args.tenant_id:
            params = {'tenant_id': args.tenant_id,
                      'project_id': args.tenant_id}
        else:
            params = {}

        compute_endpoint = get_endpoint_url_for_service(
            'compute', auth_ref, 'internal')

        volume_endpoint = get_endpoint_url_for_service(
            'volumev2', auth_ref, 'internal')

        r = s.get('%s/limits' % compute_endpoint, params=params,
                  verify=False,
                  timeout=5)

        if (r.status_code != 200):
            raise Exception("Nova returned status code %s" % str(
                r.status_code))
        nova = r.json()['limits']['absolute']

        r = s.get('%s/limits' % volume_endpoint, params=params,
                  verify=False,
                  timeout=5)

        if (r.status_code != 200):
            raise Exception(
                "Volume returned status code %s" % str(r.status_code))
        volume = r.json()['limits']['absolute']

        metric_bool('client_success', True, m_name='maas_octavia')
        status_ok(m_name='maas_octavia')
        metric('octavia_cores_quota_usage',
               'double',
               '%.3f' % (
                   max(0, nova['totalCoresUsed'] / nova[
                       'maxTotalCores'] * 100)),
               '%')
        metric('octavia_instances_quota_usage',
               'double',
               '%.3f' % (max(0, nova['totalInstancesUsed'] / nova[
                   'maxTotalInstances'] * 100)),
               '%')
        metric('octavia_ram_quota_usage',
               'double',
               '%.3f' % (
                   max(0, nova['totalRAMUsed'] / nova[
                       'maxTotalRAMSize'] * 100)),
               '%')
        metric('octavia_server_group_quota_usage',
               'double',
               '%.3f' % (max(0, nova['totalServerGroupsUsed'] / nova[
                   'maxServerGroups'] * 100)),
               '%')
        metric('octavia_volume_gb_quota_usage',
               'double',
               '%.3f' % (max(0, volume['totalGigabytesUsed'] / volume[
                   'maxTotalVolumeGigabytes'] * 100)),
               '%')
        metric('octavia_num_volume_quota_usage',
               'double',
               '%.3f' % (max(0, volume['totalVolumesUsed'] / volume[
                   'maxTotalVolumes'] * 100)),
               '%')

        # Neutron got it's limit support in Pike...

    except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
        metric_bool('client_success', False, m_name='maas_octavia')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_octavia')
        status_err(str(e), m_name='maas_octavia')
    else:
        metric_bool('client_success', True, m_name='maas_octavia')

    status_ok(m_name='maas_octavia')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)


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

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
import collections
import ipaddr
# Technically maas_common isn't third-party but our own thing but hacking
# consideres it third-party
from maas_common import get_auth_ref
from maas_common import get_cinder_api_version
from maas_common import get_keystone_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests
from requests import exceptions as exc

VOLUME_STATUSES = ['available', 'in-use', 'error']


def check(auth_ref, args):
    keystone = get_keystone_client(auth_ref)
    auth_token = keystone.auth_token
    cinder_api_version = get_cinder_api_version()
    volume_endpoint = ('{protocol}://{ip}:{port}/v{version}/{tenant}'.format(
        ip=args.ip,
        tenant=keystone.tenant_id,
        protocol=args.protocol,
        port=args.port,
        version=cinder_api_version
    ))

    s = requests.Session()

    s.headers.update(
        {'Content-type': 'application/json',
         'x-auth-token': auth_token})

    try:
        vol = s.get('%s/volumes/detail' % volume_endpoint,
                    verify=False,
                    timeout=5)
        milliseconds = vol.elapsed.total_seconds() * 1000
        snap = s.get('%s/snapshots/detail' % volume_endpoint,
                     verify=False,
                     timeout=5)
        is_up = vol.ok and snap.ok
    except (exc.ConnectionError,
            exc.HTTPError,
            exc.Timeout) as e:
        is_up = False
        metric_bool('client_success', False, m_name='maas_cinder')
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_cinder')
        status_err(str(e), m_name='maas_cinder')
    else:
        metric_bool('client_success', True, m_name='maas_cinder')
        # gather some metrics
        vol_statuses = [v['status'] for v in vol.json()['volumes']]
        vol_status_count = collections.Counter(vol_statuses)
        total_vols = len(vol.json()['volumes'])

        snap_statuses = [v['status'] for v in snap.json()['snapshots']]
        snap_status_count = collections.Counter(snap_statuses)
        total_snaps = len(snap.json()['snapshots'])

    status_ok(m_name='maas_cinder')
    metric_bool('cinder_api_local_status', is_up, m_name='maas_cinder')
    # only want to send other metrics if api is up
    if is_up:
        metric('cinder_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')
        metric('total_cinder_volumes', 'uint32', total_vols, 'volumes')
        for status in VOLUME_STATUSES:
            metric('cinder_%s_volumes' % status,
                   'uint32',
                   vol_status_count[status], 'volumes')
        metric('total_cinder_snapshots', 'uint32', total_snaps, 'snapshots')
        for status in VOLUME_STATUSES:
            metric('cinder_%s_snaps' % status,
                   'uint32',
                   snap_status_count[status], 'snapshots')


def main(args):
    auth_ref = get_auth_ref()
    check(auth_ref, args)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Check Cinder API against"
                                     " local or remote address")
    parser.add_argument('ip',
                        type=ipaddr.IPv4Address,
                        help='Cinder API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--protocol',
                        default="http",
                        help="Protocol to use for cinder end point.")
    parser.add_argument('--port',
                        default="8776",
                        help="Port the cinder service is running on.")
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

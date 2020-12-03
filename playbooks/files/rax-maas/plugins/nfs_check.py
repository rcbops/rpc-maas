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

import argparse
import shlex
import subprocess

from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def nfs_export_check():
    nfs_metrics = dict()

    output = subprocess.check_output(
        shlex.split(
            "awk -F':' '/ nfs / {print $1}' /proc/mounts"
        )
    )
    nfs_mounts = output.splitlines()
    for mount in nfs_mounts:
        mount_metrics = nfs_metrics[mount] = {'exports': 0, 'online': False}
        try:
            exports = subprocess.check_output(
                shlex.split(
                    "showmount --no-headers --exports {}".format(mount)
                )
            )
        except subprocess.CalledProcessError:
            mount_metrics['exports'] = 0
        else:
            mount_metrics['exports'] += len(exports.splitlines())

        if mount_metrics['exports'] > 0:
            mount_metrics['online'] = True

    return nfs_metrics


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='NFS exports check')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        nfs_system_check = nfs_export_check()

        # If there are no returns for the nfs check or the status is ALL
        # online the check is marked as "OK".
        status = all([i['online'] for i in nfs_system_check.values()])
        if status:
            status_ok(m_name='nfs_check')
        else:
            status_err('The state of NFS connections is degraded',
                       m_name='nfs_check')

        # Generate a general purpose metric fot the operational state of NFS.
        metric_bool('nfs_all_online', status, m_name='nfs_check')

        for key, value in nfs_system_check.items():
            # NOTE(npawelek): Generate a metric for offline exports only, which
            # will provide insight into specific volumes that are down while
            # limiting the risk of exporting too many metrics per check (50).
            if value['online'] is False:
                # NOTE(npawelek): Dashes are not valid in metric names
                sanitized_key = key.replace('-', '_')
                metric_bool('nfs_{}_online'.format(sanitized_key),
                            value['online'],
                            m_name='nfs_check')

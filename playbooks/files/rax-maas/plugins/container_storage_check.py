#!/usr/bin/env python3

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
import os

import lxc

from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def disk_partitions(container):
    """runs df in container pid/mnt/user namespace"""
    try:
        r, w = os.pipe()
        with os.fdopen(w, 'w') as fh:
            cmd = 'df -x devtmpfs -x tmpfs -x debugfs'.split()
            container.attach_wait(lxc.attach_run_command, cmd, stdout=fh)
        with os.fdopen(r) as fh:
            return fh.read().splitlines()[1:]
    except OSError:
        return []


def disk_usage(part):
    """gets usage percentage from df output lines"""
    try:
        return int(part.split()[4].rstrip('%'))
    except:
        return 0


def container_check(thresh):
    containers = lxc.list_containers()
    for container in containers:
        c = lxc.Container(container)
        if c.init_pid == -1:
            return True

        for partition in disk_partitions(c):
            percent_used = disk_usage(part=partition)
            if percent_used >= thresh:
                return False
    else:
        return True


def get_args():
    parser = argparse.ArgumentParser(description='Container storage checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument(
        '--thresh',
        required=True,
        type=int,
        help='Critical threshold'
    )
    return parser.parse_args()


def main():
    _container_check = False
    try:
        _container_check = container_check(thresh=args.thresh)
    except Exception as e:
        metric_bool(
            'container_storage_percent_used_critical',
            _container_check, m_name='maas_container'
        )
        status_err(str(e), m_name='maas_container')
    else:
        status_ok(m_name='maas_container')
        metric_bool(
            'container_storage_percent_used_critical',
            _container_check, m_name='maas_container'
        )


if __name__ == '__main__':
    args = get_args()
    with print_output(print_telegraf=args.telegraf_output):
        main()

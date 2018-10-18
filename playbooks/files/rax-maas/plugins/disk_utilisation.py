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
import shlex
import subprocess

from maas_common import metric
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def utilisation(time):
    output = subprocess.check_output(shlex.split('iostat -x -d %s 2' % time))
    device_lines = output.split('\nDevice:')[-1].strip().split('\n')[1:]
    devices = [d for d in device_lines if not d.startswith(('dm-', 'nb'))]
    devices = [d.split() for d in devices]
    utils = [(d[0], d[-1]) for d in devices if d]
    return utils

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Disk utilisation checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        try:
            utils = utilisation(5)
        except Exception as e:
            status_err(e, m_name='maas_disk_utilisation')
        else:
            status_ok(m_name='maas_disk_utilisation')
            for util in utils:
                metric('disk_utilisation_%s' % util[0], 'double', util[1], '%')

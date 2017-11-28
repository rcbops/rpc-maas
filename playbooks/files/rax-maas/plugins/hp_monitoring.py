#!/usr/bin/env python

# Copyright 2015, Rackspace US, Inc.
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
import subprocess

import maas_common


class BadOutputError(maas_common.MaaSException):
    pass


def check_command(command, startswith, endswith):
    status = 0
    try:
        output = subprocess.check_output(command)
        lines = output.split('\n')
        matches = False
        for line in lines:
            line = line.strip()
            if line.startswith(startswith):
                matches = True
                if not line.endswith(endswith):
                    break
        else:
            if matches:
                status = 1
    except Exception:
        pass
    return status


def get_chassis_status(command, item):
    return check_command((command, '-s', 'show %s' % item),
                         'Status', 'Ok')


def get_drive_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'config'),
                         'logicaldrive', 'OK)')


def get_controller_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'status'),
                         'Controller Status', 'OK')


def get_controller_cache_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'status'),
                         'Cache Status', ('OK', 'Not Configured'))


def get_controller_battery_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'status'),
                         'Battery/Capacitor Status', 'OK')


def main():

    try:
        os.stat('/usr/sbin/ssacli')
        ssacli_bin = 'ssacli'
    except Exception:
        try:
            os.stat('/usr/sbin/hpssacli')
            ssacli_bin = 'hpssacli'
        except Exception:
            maas_common.status_err('Neither ssacli or hpssacli could be found',
                                   m_name='hp_monitoring')

    status = {}
    status['hardware_processors_status'] = \
        get_chassis_status('hpasmcli', 'server')
    status['hardware_memory_status'] = get_chassis_status('hpasmcli', 'dimm')
    status['hardware_disk_status'] = get_drive_status(ssacli_bin)
    status['hardware_controller_status'] = get_controller_status(ssacli_bin)
    status['hardware_controller_cache_status'] = \
        get_controller_cache_status(ssacli_bin)
    status['hardware_controller_battery_status'] = \
        get_controller_battery_status(ssacli_bin)

    maas_common.status_ok(m_name='maas_hwvendor')
    for name, value in status.viewitems():
        maas_common.metric_bool(name, value, m_name='maas_hwvendor')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HP monitoring checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with maas_common.print_output(print_telegraf=args.telegraf_output):
        main()

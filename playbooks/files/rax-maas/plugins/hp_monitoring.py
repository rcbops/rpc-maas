#!/usr/bin/env python3

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

from ipaddress import ip_address
import maas_common
import requests


class BadOutputError(maas_common.MaaSException):
    pass


def check_command(command, startswith, endswith):
    status = 0
    try:
        output = subprocess.check_output(command)
        lines = output.decode().split('\n')
        matches = False
        for line in lines:
            line = line.strip()
            if line.startswith(startswith):
                if line.endswith(endswith):
                    matches = True
                else:
                    break
        else:
            if matches:
                status = 1
    except Exception:
        pass
    return status


def get_ilo_address(command, startswith):
    output = subprocess.check_output(command)
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if line.startswith(startswith):
            try:
                ip = line.split(':')[1].strip()
                ip_address(unicode(ip))
            except ValueError:
                maas_common.status_err("Unable to detect valid IP address.")
    return ip


def get_health_status_from_ilo(addr, s):
    try:
        url = "https://%s/rest/v1/Systems/1" % addr
        r = s.get(url, verify=False, timeout=10)
    except requests.exceptions.ConnectTimeout:
        maas_common.status_err("Timeout connecting to iLO address: %s" % url)
    else:
        if r.ok:
            return r.json().get('Oem').get('Hpe').get('AggregateHealthStatus')
        if r.status_code == 401:
            maas_common.status_err('Invalid iLO credentials. Unable to obtain '
                                   'component health status.')


def parse_component_health(component):
    if component['Status']['Health'] == 'OK':
        return 1
    else:
        return 0


def get_chassis_status(command, item):
    return check_command((command, '-s', 'show %s' % item),
                         'Status', 'Ok')


def get_powersupply_status(command, item):
    return check_command((command, '-s', 'show %s' % item),
                         'Condition', 'Ok')


def get_logicaldrive_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'config'),
                         'logicaldrive', ('OK)', 'OK, Encrypted)'))


def get_physicaldrive_status(command):
    return check_command((command, 'ctrl', 'all', 'show', 'config'),
                         'physicaldrive', ('OK)', 'OK, Encrypted)'))


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
    gen10_check = check_command(('dmidecode', '--type', 'system'),
                                'Product Name:', 'Gen10')
    if bool(gen10_check):
        ilo_address = get_ilo_address(('ipmitool', 'lan', 'print'),
                                      'IP Address   ')

        # Set requests headers and auth
        s = requests.Session()
        s.headers.update({"Content-type": "application/json"})
        user, password = args.ilo_credentials.split(':')
        s.auth = (user, password)

        # Gather health output from iLO API
        health_status = get_health_status_from_ilo(ilo_address, s)

        # Parse output
        status['hardware_processors_status'] = \
            parse_component_health(health_status['Processors'])
        status['hardware_memory_status'] = \
            parse_component_health(health_status['Memory'])
        status['hardware_powersupply_status'] = \
            parse_component_health(health_status['PowerSupplies'])
    else:
        status['hardware_processors_status'] = \
            get_chassis_status('hpasmcli', 'server')
        status['hardware_memory_status'] = \
            get_chassis_status('hpasmcli', 'dimm')
        status['hardware_powersupply_status'] = \
            get_powersupply_status('hpasmcli', 'powersupply')

    status['hardware_logicaldrive_status'] = \
        get_logicaldrive_status(ssacli_bin)
    status['hardware_physicaldrive_status'] = \
        get_physicaldrive_status(ssacli_bin)
    status['hardware_controller_status'] = get_controller_status(ssacli_bin)
    status['hardware_controller_cache_status'] = \
        get_controller_cache_status(ssacli_bin)
    status['hardware_controller_battery_status'] = \
        get_controller_battery_status(ssacli_bin)

    maas_common.status_ok(m_name='maas_hwvendor')
    for name, value in status.items():
        maas_common.metric_bool(name, value, m_name='maas_hwvendor')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='HP monitoring checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--ilo-credentials',
                        action='store',
                        default='root:calvincalvin',
                        help='iLO credentials')
    args = parser.parse_args()
    with maas_common.print_output(print_telegraf=args.telegraf_output):
        main()

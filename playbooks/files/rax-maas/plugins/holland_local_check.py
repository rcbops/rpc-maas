#!/usr/bin/env python

# Copyright 2016, Rackspace US, Inc.
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
try:
    import lxc
    lxc_module_active = True
except ImportError:
    lxc_module_active = False
    pass
import os
import shlex
import subprocess

from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def run_command(arg):
    proc = subprocess.Popen(shlex.split(arg),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False)

    out, err = proc.communicate()
    ret = proc.returncode
    return ret, out, err


def parse_args():
    parser = argparse.ArgumentParser(
        description='Check holland backup completion')
    parser.add_argument('galera_hostname',
                        help='Name of the Galera host running holland')
    parser.add_argument('holland_binary', nargs='?',
                        help='Absolute path to the holland binary',
                        default='/usr/local/bin/holland')
    parser.add_argument('holland_backupset', nargs='?',
                        help='Name of the holland backupset',
                        default='rpc_support')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    return parser.parse_args()


def print_metrics(name, size):
    metric('holland_backup_size', 'double', size, 'Megabytes')


def holland_lb_check(hostname, binary, backupset):
    backupsets = []
    container_present = True

    if lxc_module_active:
        retcode, output, err = run_command('lxc-attach -n %s -- %s lb' %
                                           (hostname, binary))
    else:
        retcode, output, err = run_command('%s lb' % binary)

    if retcode > 0:
        status_err('Could not list holland backupsets: %s' % (err),
                   m_name='maas_holland')

    for line in output.split():
        if backupset + '/' in line:
            backupname = line.split('/')[-1]
            disksize = 0

            # Determine size of the backup
            if container_present:
                retcode, output, err = \
                    run_command('lxc-attach -n %s -- '
                                'du -ks /var/backup/holland_backups/%s/%s' %
                                (hostname, backupset, backupname))
            else:
                retcode, output, err = \
                    run_command('du -ks /var/backup/holland_backups/%s/%s' %
                                (backupset, backupname))

            if retcode == 0:
                disksize = output.split()[0]

            # Populate backupset informations
            backupsets.append([backupname, disksize])

    return backupsets


def main():
    galera_hostname = args.galera_hostname
    holland_bin = args.holland_binary
    holland_bs = args.holland_backupset

    today = datetime.date.today().strftime('%Y%m%d')
    yesterday = (datetime.date.today() -
                 datetime.timedelta(days=1)).strftime('%Y%m%d')

    # Get completed Holland backup set
    backupsets = \
        holland_lb_check(galera_hostname, holland_bin, holland_bs)

    if len([backup for backup in backupsets
            if yesterday or today in backup[0]]) > 0:
        status_ok(m_name='maas_holland')
        metric_bool('holland_backup_status', True, m_name='maas_holland')
    else:
        metric_bool('holland_backup_status', False, m_name='maas_holland')
        status_err('Could not find Holland backup from %s or %s'
                   % (yesterday, today), m_name='maas_holland')

    # Print metric about last backup
    print_metrics('holland_backup_size',
                  "{0:.1f}".format(float(backupsets[-1][1]) / 1024))


if __name__ == '__main__':
    args = parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main()

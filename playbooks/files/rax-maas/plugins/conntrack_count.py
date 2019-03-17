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
import errno
try:
    import lxc
    lxc_module_active = True
except ImportError:
    lxc_module_active = False
    pass

import maas_common
import os
import subprocess
import tempfile


class MissingModuleError(maas_common.MaaSException):
    pass


def parse_args():
    parser = argparse.ArgumentParser(
        description='Check netfilter conntrack')
    parser.add_argument('--container', nargs='?',
                        help='Name of the container to check against')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    return parser.parse_args()


def get_value(path):
    try:
        with open(path) as f:
            value = f.read()
    except IOError as e:
        if e.errno == errno.ENOENT:
            msg = ('Unable to read "%s", the appropriate kernel module is '
                   'probably not loaded.' % path)
            raise MissingModuleError(msg)

    return value.strip()


def get_metrics():
    metrics = {
        'nf_conntrack_count': {
            'path': '/proc/sys/net/netfilter/nf_conntrack_count'},
        'nf_conntrack_max': {
            'path': '/proc/sys/net/netfilter/nf_conntrack_max'}}

    # Retrieve root namespace count
    for data in metrics.viewvalues():
        data['value'] = get_value(data['path'])

    # Retrieve conntrack count per namespace
    # and report the namespace with the highest count.
    # This is necessary to limit the number of metrics to report to MAAS,
    # as we can not report a metric per namespace, which by nature are
    # also volatile.
    try:
        namespaces = os.listdir('/var/run/netns')
        nscount = 0
        for ns in namespaces:
            ps = subprocess.check_output(['ip', 'netns', 'exec',
                                          ns, 'cat',
                                          '/proc/sys/net/netfilter/'
                                          'nf_conntrack_count'])
            nscount = int(ps.strip(os.linesep))

        if nscount > metrics['nf_conntrack_count']['value']:
            metrics['nf_conntrack_count']['value'] = nscount
    except OSError:
        pass

    return metrics


def get_metrics_lxc_container(container_name=''):

    # Return 0 values if we can't determine current state
    # from a container
    metrics = {
        'nf_conntrack_count': {'value': 0},
        'nf_conntrack_max': {'value': 0}}

    # Create lxc container object
    cont = lxc.Container(container_name)

    if not (cont.init_pid > 1 and
            cont.running and
            cont.state == "RUNNING"):
        raise maas_common.MaaSException('Container %s not in running state' %
                                        cont.name)

    # Check if container is even running
    try:
        with tempfile.TemporaryFile() as tmpfile:
            # Retrieve root namespace count
            if cont.attach_wait(lxc.attach_run_command,
                                ['cat',
                                 '/proc/sys/net/netfilter/nf_conntrack_count',
                                 '/proc/sys/net/netfilter/nf_conntrack_max'],
                                stdout=tmpfile,
                                stderr=tempfile.TemporaryFile()) > -1:

                tmpfile.seek(0)
                output = tmpfile.read()
                metrics = {
                    'nf_conntrack_count': {'value': output.split('\n')[0]},
                    'nf_conntrack_max': {'value': output.split('\n')[1]}}

        # Retrieve conntrack count per namespace
        # and report the namespace with the highest count.
        # This is necessary to limit the number of metrics to report to MAAS,
        # as we can not report a metric per namespace, which by nature are
        # also volatile.
        with tempfile.TemporaryFile() as nsfile:
            if cont.attach_wait(lxc.attach_run_command,
                                ['ls',
                                 '-1',
                                 '/var/run/netns'],
                                stdout=nsfile,
                                stderr=tempfile.TemporaryFile()) > -1:
                nsfile.seek(0)

                for line in nsfile.readlines():
                    ns = line.strip(os.linesep)
                    nscountfile = tempfile.TemporaryFile()

                    if cont.attach_wait(lxc.attach_run_command,
                                        ['ip', 'netns', 'exec',
                                         ns, 'cat',
                                         '/proc/sys/net/netfilter/'
                                         'nf_conntrack_count'],
                                        stdout=nscountfile,
                                        stderr=tempfile.TemporaryFile()) > -1:

                        nscountfile.seek(0)
                        nscount = int(nscountfile.read().strip(os.linesep))

                        if nscount > metrics['nf_conntrack_count']['value']:
                            metrics['nf_conntrack_count']['value'] = nscount

        return metrics

    except maas_common.MaaSException as e:
        maas_common.status_err(str(e), m_name='maas_conntrack')


def main():
    try:
        if not args.container:
            metrics = get_metrics()
        else:
            if not lxc_module_active:
                raise maas_common.MaaSException('Container monitoring '
                                                'requested but lxc-python '
                                                'pip module not installed.')
            metrics = get_metrics_lxc_container(args.container)

    except maas_common.MaaSException as e:
        maas_common.status_err(str(e), m_name='maas_conntrack')
    else:
        maas_common.status_ok(m_name='maas_conntrack')
        for name, data in metrics.viewitems():
            maas_common.metric(name, 'uint32', data['value'])


if __name__ == '__main__':
    args = parse_args()
    with maas_common.print_output(print_telegraf=args.telegraf_output):
        main()

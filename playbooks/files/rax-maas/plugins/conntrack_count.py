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
import ctypes
import errno
import os

try:
    import lxc
    lxc_module_active = True
except ImportError:
    lxc_module_active = False
    pass
from pyroute2 import netns

import maas_common


METRICS = {
    'nf_conntrack_count': {
        'path': '/proc/sys/net/netfilter/nf_conntrack_count',
        'value': 0
    },
    'nf_conntrack_max': {
        'path': '/proc/sys/net/netfilter/nf_conntrack_max',
        'value': 0
    }
}


class MissingModuleError(maas_common.MaaSException):
    pass


class NsEnter(object):
    def __init__(self, pid, ns_type, proc='/proc'):
        self.libc = ctypes.CDLL(ctypes.util.find_library('c'), use_errno=True)
        self.target_fileno = os.open(
            os.sep.join([proc, str(pid), 'ns', ns_type]), os.O_RDONLY
        )

        self.parent_fileno = os.open(
            os.sep.join([proc, 'self', 'ns', ns_type]), os.O_RDONLY
        )

    def enter(self):
        return self.libc.setns(self.target_fileno, 0)

    def __enter__(self):
        return self.enter()

    def exit(self):
        self.libc.setns(self.parent_fileno, 0)

    def __exit__(self, type, value, tb):
        return self.exit()


class NetNsExec(object):

    def __init__(self, ns):
        self.ns = ns

    def __enter__(self):
        return netns.pushns(newns=self.ns)

    def __exit__(self, exc_type, exc_val, exc_tb):
        return netns.popns()


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
            value = int(f.read().strip())
    except IOError as e:
        if e.errno == errno.ENOENT:
            msg = ('Unable to read "%s", the appropriate kernel module is '
                   'probably not loaded.' % path)
            raise MissingModuleError(msg)
    else:
        return value


def get_metrics(netns_list=None):
    """Return Metrics for contract values.

    This function will return the highest value of "nf_conntrack_count" from
    all available namespaces.

    :returns: ``dict``
    """
    for key in METRICS.keys():
        METRICS[key]['value'] = get_value(METRICS[key]['path'])

    ns_count = [METRICS['nf_conntrack_count']['value']]
    for ns in netns_list or netns.listnetns():
        with NetNsExec(ns=ns):
            ns_count.append(
                get_value(
                    path='/proc/sys/net/netfilter/nf_conntrack_count'
                )
            )

    METRICS['nf_conntrack_count']['value'] = max(ns_count)

    return METRICS


def get_metrics_lxc_container(container_name):
    # Create lxc container object
    cont = lxc.Container(container_name)
    container_pid = int(cont.init_pid)
    if not (container_pid > 1 and cont.running and cont.state == "RUNNING"):
        raise maas_common.MaaSException(
            'Container %s not in running state' % cont.name
        )

    with NsEnter(pid=container_pid, ns_type='net'):
        return get_metrics()


def main():
    try:
        if not args.container:
            metrics = get_metrics()
        else:
            if not lxc_module_active:
                raise maas_common.MaaSException(
                    'Container monitoring requested but failed. Check'
                    'lxc-python pip module not installed within the plugin'
                    'execution path.'
                )
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

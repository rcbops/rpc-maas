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
import os
import re

try:
    import lxc
    on_lxc_container = True
except ImportError:
    import socket
    on_lxc_container = False

from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from process_check_container import get_processes


def check_process_statuses(container_or_host_name, container=None):
    process_names = ['ovsdb-server', 'ovs-vswitchd',
                     'neutron-openvswitch-agent']

    if container is None:
        pid = None
    else:
        pid = container.init_pid

    # Get the processes within the neutron agent container (or a
    # compute host).
    procs = get_processes(parent_pid=pid)

    # Make a list of command lines from each PID. There's a
    # chance that one or more PIDs may have exited already and
    # this causes a NoSuchProcess exception.
    cmdlines = []
    for proc in procs:
        try:
            # In psutil 1.2.1, cmdline is an attribute, but in
            # 5.x, it's now a callable method.
            cmdline_check = getattr(proc, "cmdline", None)
            if callable(cmdline_check):
                cmdlines.append(
                    map(os.path.basename, proc.cmdline())
                )
            else:
                cmdlines.append(map(os.path.basename,
                                    proc.cmdline))
        except Exception as e:
            status_err('Error while retrieving process %s, ERROR: %s'
                       % (proc.cmdline, str(e)),
                       m_name='maas_neutron')
            pass

    # Loop through the process names provided on the command line to
    # see if ovsdb-server,  ovs-vswitchd, and neutron-openvswitch
    # exist on the system or in a container.
    # suppress some character which throw MaaS off
    # ovsdb-server and ovs-vswitchd are not directly in the command
    # line parsing so we use condition
    # `process_name in x or process_name in x[0]`
    pattern = re.compile('[^-\w]+')
    for process_name in process_names:
        matches = [x for x in cmdlines
                   if process_name in x or (
                       len(x) > 0 and process_name in x[0]
                   )
                   ]

        metric_bool('%s_process_status' % (
                    pattern.sub('', process_name)
                    ),
                    len(matches) > 0)


def check(args):

    if on_lxc_container:
        containers = lxc.list_containers()
        neutron_agent_containers = []
        for container in containers:
            if 'neutron_agents' in container:
                metric_bool('agents_found',
                            True, m_name='maas_neutron')
                neutron_agent_containers.append(container)

        if len(neutron_agent_containers) == 0:
            metric_bool('agents_found', False, m_name='maas_neutron')
            status_err('no running neutron agents containers found',
                       m_name='maas_neutron')
            return

        for neutron_agent_container in neutron_agent_containers:
            # Get the neutron_agent_container's init PID.
            try:
                c = lxc.Container(neutron_agent_container)
                # If the container wasn't found, exit now.
                if c.init_pid == -1:
                    metric_bool('container_success',
                                False,
                                m_name='maas_neutron_agent_container')
                    status_err(
                        'Could not find PID for container {}'.format(
                            neutron_agent_container
                        ),
                        m_name='maas_neutron_agent_container'
                    )
            except (Exception, SystemError) as e:
                metric_bool('container_success', False,
                            m_name='maas_neutron_agent_container')
                status_err(
                    'Container lookup failed on "{}". ERROR: "{}"'
                    .format(
                        neutron_agent_container,
                        e
                    ),
                    m_name='maas_neutron_agent_container'
                )
            else:
                metric_bool('container_success', True,
                            m_name='maas_neutron_agent_container')

            # c is the lxc container instance of this
            # neutron_agent_container
            check_process_statuses(neutron_agent_container, c)
    else:
        ovs_agent_host = socket.gethostname()
        check_process_statuses(ovs_agent_host)


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check neutron OVS'
                                                 'agents running')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

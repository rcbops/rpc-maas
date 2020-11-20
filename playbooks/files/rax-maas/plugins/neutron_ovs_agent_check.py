#!/usr/bin/env python3
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

from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err, status_err_no_exit, status_ok
from process_check_host import get_processes


def check_process_statuses(container_or_host_name, container=None):
    process_names = ['ovsdb-server', 'ovs-vswitchd']

    if container is None:
        pid = None
    else:
        pid = container.init_pid

    # Get processes within the neutron container or baremetal host
    procs = get_processes(parent_pid=pid)

    # Make a list of command lines from each PID. There's a chance that
    # one or more PIDs may have exited already which results in a
    # NoSuchProcess exception.
    cmdlines = []
    for proc in procs:
        try:
            # In psutil 1.2.1, cmdline is an attribute, but in
            # 5.x, it's now a callable method.
            cmdline_check = getattr(proc, "cmdline", None)
            if callable(cmdline_check):
                cmdline_check_value = proc.cmdline()
            else:
                cmdline_check_value = proc.cmdline
            cmdlines.append(cmdline_check_value)
        except Exception as e:
            status_err_no_exit('Error while retrieving process %s, ERROR: %s'
                               % (cmdline_check_value, str(e)),
                               m_name='maas_neutron')

    # Loop through the process names provided on the command line to
    # see if ovsdb-server, ovs-vswitchd exist on the system or in a
    # container.
    pattern = re.compile('[^-\w]+')
    for process_name in process_names:
        cur_proc_count = 0
        for cmdline in cmdlines:
            if process_name in cmdline:
                cur_proc_count = cur_proc_count + 1

        metric_bool('%s_process_status' % (
                    pattern.sub('', process_name)
                    ),
                    cur_proc_count > 0)


def check(args):
    neutron = get_openstack_client('network')

    try:
        # Gather neutron agent states
        if args.host:
            agents = [i for i in neutron.agents(host=args.host)]
        elif args.fqdn:
            agents = [i for i in neutron.agents(host=args.fqdn)]
        else:
            agents = [i for i in neutron.agents()]

    # An API status metric is not gathered so catch any exception
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_neutron')
        metric('%s_status' % "neutron-openvswitch-agent",
               'string',
               '%s cannot reach API' % "neutron-openvswitch-agent",
               m_name='maas_neutron')
        status_err_no_exit(str(e), m_name='maas_neutron')
        return
    else:
        metric_bool('client_success', True, m_name='maas_neutron')

    try:
        ovs_agent = next(
            a for a in agents if 'openvswitch' in a['binary']
        )
    except StopIteration:
        status_err("No host(s) found in the agents list",
                   m_name='maas_neutron')
    else:
        # Return all the things
        status_ok(m_name='maas_neutron')

        agent_is_up = "Yes"
        if ovs_agent['is_admin_state_up'] and not ovs_agent['is_alive']:
            agent_is_up = "No"

        if args.host:
            name = '%s_status' % ovs_agent['binary']
        elif args.fqdn:
            name = '%s_status' % ovs_agent['binary']
        else:
            name = '%s_%s_on_host_%s' % (ovs_agent['binary'],
                                         ovs_agent['id'],
                                         ovs_agent['host'])

        metric(name, 'string', agent_is_up, m_name='maas_neutron')

    if on_lxc_container:
        all_containers = lxc.list_containers()
        neutron_containers_list = []
        neutron_agent_containers_list = []

        # NOTE(npawelek): The neutron container architecture was
        # refactored in recent versions removing all neutron containers
        # with the exception of one, or even using baremetal directly.
        # Since logic is looking for the presence of LXC, we do not need
        # to account for baremetal here.
        for container in all_containers:
            if 'neutron_agents' in container:
                neutron_agent_containers_list.append(container)

            if 'neutron' in container:
                neutron_containers_list.append(container)

        if len(neutron_containers_list) == 1 and \
                'neutron_server' in neutron_containers_list[0]:
            valid_containers = neutron_containers_list
        elif len(neutron_agent_containers_list) > 0:
            valid_containers = neutron_agent_containers_list
        else:
            valid_containers = 0

        if len(valid_containers) == 0:
            status_err('no neutron agent or server containers found',
                       m_name='maas_neutron')
            return

        for container in valid_containers:
            # Get the neutron_agent_container's init PID.
            try:
                c = lxc.Container(container)
                # If the container wasn't found, exit now.
                if c.init_pid == -1:
                    metric_bool('container_success',
                                False,
                                m_name='maas_neutron')
                    status_err(
                        'Could not find PID for container {}'.format(
                            container
                        ),
                        m_name='maas_neutron'
                    )
            except (Exception, SystemError) as e:
                metric_bool('container_success', False,
                            m_name='maas_neutron')
                status_err(
                    'Container lookup failed on "{}". ERROR: "{}"'
                    .format(
                        container,
                        e
                    ),
                    m_name='maas_neutron'
                )
            else:
                metric_bool('container_success', True,
                            m_name='maas_neutron')

                # c is the lxc container instance of this
                # neutron_agent_container
                check_process_statuses(container, c)
    else:
        ovs_agent_host = socket.gethostname()
        check_process_statuses(ovs_agent_host)


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check neutron OVS'
                                                 'agents running')
    parser.add_argument('hostname',
                        type=str,
                        help='Neutron API hostname or IP address')
    parser.add_argument('--host',
                        type=str,
                        help='Only return metrics for specified host',
                        default=None)
    parser.add_argument('--fqdn',
                        type=str,
                        help='Only return metrics for specified fqdn',
                        default=None)
    parser.add_argument('--protocol',
                        type=str,
                        default='http',
                        help='Protocol for client requests')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

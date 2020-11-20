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
import subprocess
import re


from maas_common import metric
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from maas_common import MaaSException


class BadOutputError(MaaSException):
    pass


def check_command(command, param1, param2=None):
    if param2:
        output = subprocess.check_output([command, param1, param2])
    else:
        output = subprocess.check_output([command, param1])

    if not output:
        status_err('No output received from pacemaker. Cannot gather metrics.')
        raise BadOutputError(
            'The output was not in the expected format:\n%s' % output)

    return output.decode()


# determine nodes status, call "pcs status nodes" command
def get_nodes_status():

    output = check_command('pcs', 'status', 'nodes')
    lines = output.split('\n')
    has_metrics = False
    for line in lines:
        if line.strip().startswith('Standby') or line.strip().startswith(
                'Offline'):
            splitline = line.strip().split(': ')
            if len(splitline) > 1:
                message = "Pacemaker node standby/offline: " + splitline[1]
                metric('pacemaker_status_nodes', 'string', message)
                has_metrics = True
    if not has_metrics:
        metric('pacemaker_status_nodes', 'string',
               "Pacemaker node status is OK")


# check "pcs status". If there are any failures, warnings, or notices,
# return the whole output.
def check_for_failed_actions():

    output = check_command('pcs', 'status')
    pattern = re.compile(
        "Failed|Stopped|Notice|Fail|Error|Warning|Faulty", flags=re.IGNORECASE)
    bad_things_happened = re.search(pattern, output)

    if bad_things_happened:
        metric('pacemaker_failed_actions', 'string',
               'Errors in pacemaker cluster')
    else:
        metric('pacemaker_failed_actions', 'string', 'Pacemaker cluster is OK')


def check_for_failed_resources():

    output = check_command('pcs', 'status', 'resources')
    pattern = re.compile(
        "Failed|Stopped|Notice|Fail|Error|Warning|Faulty", flags=re.IGNORECASE)
    bad_things_happened = re.search(pattern, output)

    has_metrics = False

    if bad_things_happened:
        lines = output.split('\n')

        for index in xrange(len(lines)):
            if lines[index].strip().startswith('Stopped'):
                if lines[index - 1]:
                    message = "Stopped resource: " + lines[index - 1]
                    metric('pacemaker_resource_stop', 'string', message)
                    has_metrics = True

    if(has_metrics is False):
        metric('pacemaker_resource_stop', 'string',
               "Pacemaker resources are OK")


if __name__ == '__main__':
    with print_output():
        try:
            get_nodes_status()
            check_for_failed_actions()
            check_for_failed_resources()
        except Exception as e:
            status_err(e)
        else:
            status_ok()

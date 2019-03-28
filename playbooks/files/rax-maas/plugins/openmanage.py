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
import re
import subprocess

from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok

SUPPORTED_VERSIONS = set(["7.1.0", "7.4.0", "8.3.0", "8.4.0", "9.1.0",
                          "9.2.0"])
OM_PATTERN = '(?:%(field)s)\s+:\s+(%(group_pattern)s)'
CHASSIS = re.compile(OM_PATTERN % {'field': '^Health', 'group_pattern': '\w+'},
                     re.MULTILINE)
STORAGE = re.compile(OM_PATTERN % {'field': '^Status', 'group_pattern': '\w+'},
                     re.MULTILINE)
regex = {'storage': STORAGE, 'chassis': CHASSIS, 'pwrsupplies': STORAGE}


def hardware_report(report_type, report_request):
    """Return the report as a string."""
    return subprocess.check_output(['/opt/dell/srvadmin/bin/omreport',
                                    report_type,
                                    report_request])


def all_okay(report, regex_find):
    """Determine if the installed health and status fields are okay.

    :returns: True if all "Ok", False otherwise
    :rtype: bool
    """
    fields = regex_find.findall(report)
    if not fields:
        status_err('There were no Health or Status fields to check.',
                   m_name='maas_hwvendor')
    return all(v.lower() == 'ok' for v in fields)


def check_openmanage_version():
    """Error early if the version of OpenManage is not supported."""
    try:
        # Because of
        # https://github.com/rcbops/rcbops-maas/issues/82#issuecomment-52315709
        # we need to redirect sdterr to stdout just so MaaS does not see any
        # extra output
        output = subprocess.check_output(['/opt/dell/srvadmin/bin/omconfig',
                                          'about'],
                                         stderr=subprocess.STDOUT)
    except OSError:
        # OSError happens when subprocess cannot find the executable to run
        status_err('The OpenManage tools do not appear to be installed.',
                   m_name='maas_hwvendor')
    except subprocess.CalledProcessError as e:
        status_err(str(e), m_name='maas_hwvendor')

    match = re.search(OM_PATTERN % {'field': 'Version',
                                    'group_pattern': '[0-9.]+'},
                      output)
    if not match:
        status_err('Could not find the version information',
                   m_name='maas_hwvendor')

    version = match.groups()[0]
    if version not in SUPPORTED_VERSIONS:
        status_err(
            'Expected version in %s to be installed but found %s'
            % (SUPPORTED_VERSIONS, version),
            m_name='maas_hwvendor'
        )


def main(args):
    if len(args.omc) != 2:
        args = ' '.join(args.omc)
        status_err(
            'Requires 2 arguments, arguments provided: "%s"' % args,
            m_name='maas_hwvendor'
        )

    report_type = args.omc[0].lower()
    report_request = args.omc[1].lower()

    # If we're not using the correct version of OpenManage, error out
    check_openmanage_version()

    try:
        report = hardware_report(report_type, report_request)
    except (OSError, subprocess.CalledProcessError) as e:
        metric_bool('hardware_%s_status' % report_request, False)
        status_err(str(e), m_name='maas_hwvendor')

    status_ok(m_name='maas_hwvendor')
    if report_request == 'pwrsupplies':
        metric_bool('hardware_%s_status' % report_request,
                    all_okay(report, regex[report_request]))
    else:
        metric_bool('hardware_%s_status' % report_request,
                    all_okay(report, regex[report_type]))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Openmanage Checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('omc',
                        nargs='+',
                        help='Run OpenManage checks ["type", "request"]')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

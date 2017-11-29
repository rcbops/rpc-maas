#!/usr/bin/env python

# Copyright 2017, Rackspace US, Inc.
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

from log_file_watcher import LogWatcher

from maas_common import metric_bool
from maas_common import print_output
from maas_common import status


def critical_notification_callback(filename, lines):
    for line in lines:
        if 'CRITICAL' in line or 'critical' in line:
            status('critical', 'CRITICAL log line found in %s: %s' % (
                filename, line.strip()
            ))
            metric_bool("critical_line_found", True)


def main(args):
    l = LogWatcher("/var/log/", critical_notification_callback,
                   matching_file_names=['demo.log']
                   )
    l.loop(async=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Alert CRITICAL lines in /var/log/demo.log')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

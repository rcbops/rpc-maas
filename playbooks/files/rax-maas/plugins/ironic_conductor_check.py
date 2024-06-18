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

from maas_common import metric_bool
from maas_common import print_output
import psutil


def check(args):

    # NOTE(npawelek): API calls for conductor status are only available
    # in ironic v1.49 and onward. Instead, we look for the process
    # directly until it becomes available within the API.
    name = "ironic-conductor_status"
    for proc in psutil.process_iter():
        if 'ironic-conducto' in proc.name():
            metric_bool(name, True)
            break
    else:
        metric_bool(name, False)


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Ironic conductor status')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

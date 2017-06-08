#!/usr/bin/env python
# Copyright 2017, Rackspace US, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in witing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import subprocess

import yaml


BASE_PATH = '/etc/rackspace-monitoring-agent.conf.d'
RUN_VENV = '/usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh'


def str2bool(boolean):
    if boolean.lower() in ("yes", "true", "1"):
        return True
    elif boolean.lower() in ("no", "false", "0"):
        return False
    else:
        raise BaseException('Not a Boolean')


def load_yaml(check_file):
    with open(check_file) as f:
        return yaml.load(f.read())


def run_details(detail_args):
    args = detail_args.get('args')
    if args:
        args.insert(0, RUN_VENV)
        args.insert(2, '--telegraf-output')
        with open(os.devnull, 'w') as null:
            subprocess.call(args, stderr=null)


def main():
    for _, _, items in os.walk(BASE_PATH):
        for item in items:
            check_load = load_yaml(os.path.join(BASE_PATH, item))
            if not str2bool(boolean=check_load.get('disabled')):
                details = check_load.get('details')
                if details:
                    run_details(detail_args=details)


if __name__ == '__main__':
    main()

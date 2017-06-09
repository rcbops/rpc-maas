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

import multiprocessing
import os
import subprocess

import yaml


BASE_PATH = '/etc/rackspace-monitoring-agent.conf.d'
RUN_VENV = '/usr/lib/rackspace-monitoring-agent/plugins/run_plugin_in_venv.sh'

RETURN_QUEUE = multiprocessing.Queue()


class Runner:
    def __init__(self):
        self.queue = multiprocessing.JoinableQueue()
        self.processes = [
            multiprocessing.Process(target=self.run_details)
            for _ in range(2)
        ]
        for p in self.processes:
            p.start()

    def put(self, item):
        self.queue.put(item)

    def run_details(self):
        while True:
            detail_args = self.queue.get()
            if not detail_args:
                break

            detail_args.insert(0, RUN_VENV)
            detail_args.insert(2, '--telegraf-output')
            with open(os.devnull, 'w') as null:
                process = subprocess.Popen(
                    ' '.join(detail_args),
                    stdout=subprocess.PIPE,
                    stderr=null,
                    executable='/bin/bash',
                    shell=True
                )

            output, error = process.communicate()
            if process.returncode in [0]:
                RETURN_QUEUE.put(output.strip())
            else:
                print(error, output, ' '.join(detail_args))

            self.queue.task_done()

    def terminate(self):
        self.queue.join()
        for p in self.processes:
            p.terminate()


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


def main():
    r = Runner()
    try:
        for _, _, items in os.walk(BASE_PATH):
            for item in items:
                check_load = load_yaml(os.path.join(BASE_PATH, item))
                if not str2bool(boolean=check_load.get('disabled')):
                    details = check_load.get('details')
                    if isinstance(details, dict) and 'args' in details:
                        r.put(item=details['args'])
    finally:
        r.terminate()

    while True:
        try:
            q_item = RETURN_QUEUE.get(timeout=1)
        except Exception:
            break
        else:
            print(q_item)


if __name__ == '__main__':
    main()

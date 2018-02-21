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
import numpy as np
import os
import time
import yaml

import maas_common
from maas_common import status_err, status_ok, metric

import rally
from rally.api import API

from influxdb import InfluxDBClient

PLUGIN_CONF = '/usr/lib/rackspace-monitoring-agent/plugins/rally/config.yaml'
PLUGIN_PATH = '/usr/lib/rackspace-monitoring-agent/plugins/rally/plugins/'
TASKS_PATH = '/usr/lib/rackspace-monitoring-agent/plugins/rally/tasks/'
LOCKS_PATH = '/var/lock/maas_rally'


class ParseError(maas_common.MaaSException):
    pass


class CommandNotRecognized(maas_common.MaaSException):
    pass


def send_metrics_to_influxdb():
    with open(PLUGIN_CONF, 'r') as stream:
        try:
            plugin_config = yaml.safe_load(stream)
            influx_config = plugin_config['influxdb']
            influx_host = influx_config['host']
            influx_port = influx_config['port']
            influx_database = influx_config['database']
            influx_user = influx_config['user']
            influx_password = influx_config['password']
            tags = influx_config['tags']
        except:
            status_err('Error reading influxdb config for rally plugin.',
                       m_name='maas_rally')

    client = InfluxDBClient(influx_host,
                            influx_port,
                            influx_user,
                            influx_password,
                            influx_database)

    influx_data = {}
    influx_data['measurement'] = args.task
    influx_data['tags'] = tags
    influx_data['fields'] = dict((k, float(v)) for k, v in
                                 maas_common.TELEGRAF_METRICS['variables']
                                 .iteritems())

    client.write_points([influx_data])


def make_parser():
    parser = argparse.ArgumentParser(
        description='Execute rally performance scenario and print the results'
    )
    parser.add_argument('task',
                        help='Which task definition to execute.  The task '
                             'definition must exist in {{ maas_plugin_dir }}/ '
                             'tasks/<TASKNAME>.yml. \n'
                             'Examples: "keystone", "nova", etc.')
    parser.add_argument('-c', '--concurrency',
                        type=int,
                        help='Number of tasks to run in parallel')
    parser.add_argument('-e', '--extra_vars',
                        action='append',
                        help='Extra variable to pass to the Rally task in key='
                             'value format.  May be specified multiple times. '
                             'Example: "-e size=2 -e image_name=\'^cirros$\'"')
    parser.add_argument('-t', '--times',
                        type=int,
                        help='Number of times to execute the task')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--influxdb',
                        action='store_true',
                        default=False,
                        help='Send output to influxdb')
    return parser


def parse_task_results(task_result):
    # This expects the format returned by `rally task results <UUID>`
    action_data = {}
    action_data[args.task + '_total'] = list()
    for iteration in task_result['result']:
        iteration_total_duration = 0
        for action in iteration['atomic_actions'].keys():
            action_duration = iteration['atomic_actions'][action]
            iteration_total_duration += action_duration
            if action not in action_data:
                action_data[action] = list()
            action_data[action].append(action_duration)
        action_data[args.task + '_total'].append(iteration_total_duration)

    # Quota exceeded would be a typical error here
    if task_result['result'][0]['error']:
        status_err(' '.join(task_result['result'][0]['error']),
                   m_name='maas_rally')

    status_ok(m_name='maas_rally')

    metric('rally_load_duration', 'double',
           '{:.2f}'.format(task_result['load_duration']))
    metric('rally_full_duration', 'double',
           '{:.2f}'.format(task_result['full_duration']))

    metric('rally_sample_count', 'uint32',
           '{}'.format(task_result['key']['kw']['runner']['times']))
    metric('rally_sample_concurrency', 'uint32',
           '{}'.format(task_result['key']['kw']['runner']['concurrency']))

    for action in action_data.keys():
        metric('{}_min'.format(action), 'double',
               '{:.2f}'.format(np.amin(action_data[action])))
        metric('{}_max'.format(action), 'double',
               '{:.2f}'.format(np.amax(action_data[action])))
        metric('{}_median'.format(action), 'double',
               '{:.2f}'.format(np.median(action_data[action])))
        metric('{}_mean'.format(action), 'double',
               '{:.2f}'.format(np.mean(action_data[action])))

        metric('{}_90pctl'.format(action), 'double',
               '{:.2f}'.format(np.percentile(action_data[action], 90)))
        metric('{}_95pctl'.format(action), 'double',
               '{:.2f}'.format(np.percentile(action_data[action], 95)))


def main():
    start = time.time()

    # Ensure we can find the task definition
    tasks_path = os.path.realpath(TASKS_PATH)
    task_file = tasks_path + '/' + args.task + '.yml'
    if not os.path.isfile(task_file):
        status_err('Unable to locate task definition '
                   'for {} in {}'.format(args.task, tasks_path),
                   m_name='maas_rally')

    if not os.path.exists(LOCKS_PATH):
        os.makedirs(LOCKS_PATH)

    rapi = API()

    task_obj = rapi.task.create(args.task, [args.task])
    task_uuid = task_obj['uuid']

    LOCK_PATH = LOCKS_PATH + '/' + args.task + '/'
    if os.path.exists(LOCK_PATH):
        lock_uuid = os.listdir(LOCK_PATH)[0]
        lock_mtime = os.stat(LOCK_PATH + lock_uuid)[8]
        lock_duration = time.time() - lock_mtime
        try:
            task_status = rapi.task.get(lock_uuid)['status']
            if task_status == 'finished':
                os.rmdir(LOCK_PATH + '/' + lock_uuid)
            elif task_status == 'init' and lock_duration > 30:
                os.rmdir(LOCK_PATH + '/' + lock_uuid)
            else:
                lock_mtime_str = time.strftime('%H:%M:%S %Y-%m-%d %Z',
                                               time.localtime(lock_mtime))
                status_err("Unable to get lock for {} - locked by "
                           "task {} at {}.".format(args.task,
                                                   lock_uuid,
                                                   lock_mtime_str),
                           m_name='maas_rally')
        except rally.exceptions.TaskNotFound:
            os.rmdir(LOCK_PATH + '/' + lock_uuid)
    else:
        os.mkdir(LOCK_PATH)

    os.mkdir(LOCK_PATH + '/' + task_uuid)

    task_args = {}
    if args.times is not None:
        task_args['times'] = args.times
    if args.concurrency is not None:
        task_args['concurrency'] = args.concurrency
    if args.extra_vars is not None:
        for extra_var in args.extra_vars:
            k, v = extra_var.lstrip().split('=')
            task_args.update({k: v})

    with open(task_file) as f:
        input_task = f.read()
        task_dir = os.path.expanduser(
            os.path.dirname(task_file)) or "./"
        rendered_task = rapi.task.render_template(input_task,
                                                  task_dir,
                                                  **task_args)

    parsed_task = yaml.safe_load(rendered_task)

    rally.common.plugin.discover.load_plugins(PLUGIN_PATH)
    rally.plugins.load()
    rapi.task.start(args.task, parsed_task, task_obj)

    # This is the format returned by `rally task results <UUID>`
    results = [{"key": x["key"], "result": x["data"]["raw"],
                "sla": x["data"]["sla"],
                "hooks": x["data"].get("hooks", []),
                "load_duration": x["data"]["load_duration"],
                "full_duration": x["data"]["full_duration"],
                "created_at": x.get("created_at").strftime(
                    "%Y-%d-%mT%H:%M:%S")}
               for x in task_obj.get_results()][0]

    parse_task_results(results)

    os.rmdir(LOCK_PATH + '/' + task_uuid)
    os.rmdir(LOCK_PATH)

    end = time.time()
    metric('maas_check_duration', 'double', "{:.2f}".format((end - start) * 1))

    if args.influxdb:
        send_metrics_to_influxdb()

    return


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    with maas_common.print_output(print_telegraf=args.telegraf_output):
        main()

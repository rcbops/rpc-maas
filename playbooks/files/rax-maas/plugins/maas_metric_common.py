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

import contextlib
import logging
import sys
import traceback

from monitorstack.common import formatters


STATUS = ''
METRICS = list()
TELEGRAF_ENABLED = False
TELEGRAF_METRICS = {
    'variables': dict(),
    'meta': {
        'rpc_maas': True  # This should use some form of a job number
    }
}


def _telegraf_metric_name(name=None, m_name=None):
    global TELEGRAF_METRICS
    if 'measurement_name' in TELEGRAF_METRICS:
        return
    elif m_name:
        pass
    elif name and not m_name:
        m_name = '_'.join(name.split('_')[:3]).replace('-', '_')
    elif not name and not m_name:
        raise SystemExit('A name or m_name option must be provided')

    TELEGRAF_METRICS['measurement_name'] = m_name


def status(status, message, force_print=False):
    global STATUS
    if status in ('ok', 'warn', 'err'):
        raise ValueError('The status "%s" is not allowed because it creates a '
                         'metric called legacy_state' % status)
    status_line = 'status %s' % status
    if message is not None:
        status_line = ' '.join((status_line, str(message)))
    status_line = status_line.replace('\n', '\\n')
    STATUS = status_line
    if force_print:
        print(STATUS)


def status_err(message=None, force_print=False, exception=None, m_name=None):
    _telegraf_metric_name(m_name=m_name)
    if exception:
        # a status message cannot exceed 256 characters
        # 'error ' plus up to 250 from the end of the exception
        message = message[-250:]
    status('error', message, force_print=force_print)
    if exception:
        raise exception
    if TELEGRAF_ENABLED:
        sys.exit(0)
    else:
        sys.exit(1)


def status_ok(message=None, force_print=False, m_name=None):
    status('okay', message, force_print=force_print)
    _telegraf_metric_name(m_name=m_name)


def metric(name, metric_type, value, unit=None, m_name=None):
    global METRICS
    global TELEGRAF_METRICS
    if 'measurement_name' not in TELEGRAF_METRICS:
        _telegraf_metric_name(name=name, m_name=m_name)

    if len(METRICS) > 49:
        status_err('Maximum of 50 metrics per check', m_name='maas')

    metric_line = 'metric %s %s %s' % (name, metric_type, value)
    if unit is not None:
        metric_line = ' '.join((metric_line, unit))

    metric_line = metric_line.replace('\n', '\\n')
    METRICS.append(metric_line)
    variables = TELEGRAF_METRICS['variables']
    variables[name] = value


def metric_bool(name, success, m_name=None):
    value = success and 1 or 0
    metric(name, 'uint32', value, m_name=m_name)


try:
    logging.basicConfig(filename='/var/log/maas_plugins.log',
                        format='%(asctime)s %(levelname)s: %(message)s')
except IOError as e:
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s')
    logging.error('An error occurred accessing /var/log/maas_plugins.log. %s' %
                  e)


@contextlib.contextmanager
def print_output(print_telegraf=False):
    if print_telegraf:
        global TELEGRAF_ENABLED
        TELEGRAF_ENABLED = True
    try:
        yield
    except SystemExit as e:
        if print_telegraf:
            TELEGRAF_METRICS['message'] = STATUS
            formatters.write_telegraf(TELEGRAF_METRICS)
        else:
            if STATUS:
                print(STATUS)
        raise
    except Exception as e:
        logging.exception('The plugin %s has failed with an unhandled '
                          'exception', sys.argv[0])
        status_err(traceback.format_exc(), force_print=True, exception=e,
                   m_name='maas')
    else:
        if print_telegraf:
            TELEGRAF_METRICS['message'] = STATUS
            formatters.write_telegraf(TELEGRAF_METRICS)
        else:
            if STATUS:
                print(STATUS)
            for metric in METRICS:
                print(metric)

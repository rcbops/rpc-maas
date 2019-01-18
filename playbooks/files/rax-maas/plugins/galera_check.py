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
import shlex
import subprocess

from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok


def galera_check(arg):
    proc = subprocess.Popen(shlex.split(arg),
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            shell=False)

    out, err = proc.communicate()
    ret = proc.returncode
    return ret, out, err


def generate_query(host, port, output_type='status'):
    if host:
        host = ' -h %s' % host
    else:
        host = ''

    if port:
        port = ' -P %s' % port
    else:
        port = ''
    if output_type == 'status':
        return ('/usr/bin/mysql --defaults-file=/root/.my.cnf '
                '%s%s -e "SHOW GLOBAL STATUS"') % (host, port)
    elif output_type == 'variables':
        return ('/usr/bin/mysql --defaults-file=/root/.my.cnf '
                '%s%s -e "SHOW GLOBAL VARIABLES"') % (host, port)


def parse_args():
    parser = argparse.ArgumentParser(description='Galera checks')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('-H',
                        '--host',
                        action='store',
                        dest='host',
                        default=None,
                        help='Host to override the defaults with')
    parser.add_argument('-P',
                        '--port',
                        action='store',
                        dest='port',
                        default=None,
                        help='Port to override the defauults with')
    return parser.parse_args()


def print_metrics(replica_status):
    status_ok(m_name='maas_galera')
    metric('wsrep_replicated_bytes', 'int64',
           replica_status['wsrep_replicated_bytes'], 'bytes')
    metric('wsrep_received_bytes', 'int64',
           replica_status['wsrep_received_bytes'], 'bytes')
    metric('wsrep_commit_window_size', 'double',
           replica_status['wsrep_commit_window'], 'sequence_delta')
    metric('wsrep_cluster_size', 'int64',
           replica_status['wsrep_cluster_size'], 'nodes')
    metric('queries_per_second', 'int64',
           replica_status['Queries'], 'qps')
    metric('wsrep_cluster_state_uuid', 'string',
           replica_status['wsrep_cluster_state_uuid'])
    metric('wsrep_cluster_status', 'string',
           replica_status['wsrep_cluster_status'])
    metric('wsrep_local_state_uuid', 'string',
           replica_status['wsrep_local_state_uuid'])
    metric('wsrep_local_state_comment', 'string',
           replica_status['wsrep_local_state_comment'])
    metric('mysql_max_configured_connections', 'int64',
           replica_status['max_connections'], 'connections')
    metric('mysql_current_connections', 'int64',
           replica_status['Threads_connected'], 'connections')
    metric('mysql_max_seen_connections', 'int64',
           replica_status['Max_used_connections'], 'connections')
    metric('num_of_open_files', 'int64',
           replica_status['Open_files'], 'files')
    metric('open_files_limit', 'int64',
           replica_status['open_files_limit'], 'files')
    metric('innodb_row_lock_time_avg', 'int64',
           replica_status['Innodb_row_lock_time_avg'], 'milliseconds')
    metric('innodb_deadlocks', 'int64',
           replica_status.get('Innodb_deadlocks', 0), 'deadlocks')
    metric('access_denied_errors', 'int64',
           replica_status['Access_denied_errors'], 'access_denied_errors')
    metric('aborted_clients', 'int64',
           replica_status['Aborted_clients'], 'aborted_clients')
    metric('aborted_connects', 'int64',
           replica_status['Aborted_connects'], 'aborted_connects')


def main():
    replica_status = {}
    for output_type in ['status', 'variables']:
        retcode, output, err = galera_check(
            generate_query(options.host, options.port, output_type=output_type)
        )

        if retcode > 0:
            metric_bool('client_success', False, m_name='maas_galera')
            status_err(err, m_name='maas_galera')

        if not output:
            metric_bool('client_success', False, m_name='maas_galera')
            status_err('No output received from mysql. Cannot gather metrics.',
                       m_name='maas_galera')

        show_list = output.split('\n')[1:-1]
        for i in show_list:
            replica_status[i.split('\t')[0]] = i.split('\t')[1]

    if replica_status['wsrep_cluster_status'] != "Primary":
        metric_bool('client_success', False, m_name='maas_galera')
        status_err("there is a partition in the cluster",
                   m_name='maas_galera')

    if (replica_status['wsrep_local_state_uuid'] !=
            replica_status['wsrep_cluster_state_uuid']):
        metric_bool('client_success', False, m_name='maas_galera')
        status_err("the local node is out of sync", m_name='maas_galera')

    if (int(replica_status['wsrep_local_state']) == 4 and
            replica_status['wsrep_local_state_comment'] == "Synced"):
        print_metrics(replica_status)


if __name__ == '__main__':
    args = options = parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main()

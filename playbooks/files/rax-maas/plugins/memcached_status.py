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

import ipaddr
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_ok
import memcache


MEMCACHE_METRICS = {'total_items': 'items',
                    'get_hits': 'cache_hits',
                    'get_misses': 'cache_misses',
                    'curr_connections': 'connections'}


def item_stats(host, port):
    """Check the stats for items and connection status."""

    stats = None
    try:
        mc = memcache.Client(['%s:%s' % (host, port)])
        stats = mc.get_stats()[0][1]
    except IndexError:
        raise
    finally:
        return stats


def main(args):

    bind_ip = str(args.ip)
    port = args.port
    is_up = True

    try:
        stats = item_stats(bind_ip, port)
    except (TypeError, IndexError):
        is_up = False
        metric_bool('client_success', False, m_name='maas_memcached')
    else:
        is_up = True
        metric_bool('client_success', True, m_name='maas_memcached')

    status_ok(m_name='maas_memcached')
    metric_bool('memcache_api_local_status', is_up, m_name='maas_memcached')
    if is_up:
        for m, u in MEMCACHE_METRICS.iteritems():
            metric('memcache_%s' % m, 'uint64', stats[m], u)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check memcached status')
    parser.add_argument('ip', type=ipaddr.IPv4Address,
                        help='memcached IP address.')
    parser.add_argument('--port', type=int,
                        default=11211, help='memcached port.')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

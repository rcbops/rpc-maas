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

import datetime
import json
import optparse
import os
import re
import requests
import sys

from maas_common import metric, status_ok, status_err, print_output


def get_elasticsearch_bind_host():
    """Get the bindhost for elasticsearch if we can read the config."""
    config = '/etc/elasticsearch/elasticsearch.yml'
    if not os.path.exists(config):
        return 'localhost'

    with open(config) as fd:
        contents = fd.readlines()
    bind_host_re = re.compile('^network\.bind_host:\s+([0-9\.]+)\s+')
    hosts = filter(bind_host_re.match, contents)
    if not hosts:
        raise SystemExit(False)
    match = bind_host_re.match(hosts[-1])
    return match.groups()[0]

ES_PORT = '9200'
ELASTICSEARCH = None


def json_querystring(query_string, sort=None):
    """Generate the JSON data for a query_string query."""
    query_dict = {'query': {'query_string': query_string}}
    if sort:
        query_dict['sort'] = sort
    return json.dumps(query_dict)


def json_filter(filtered_query):
    """Generate the JSON data for a filtered query."""
    return json.dumps({'query': {'filtered': filtered_query}})


def search_url_for(index=None):
    """Generate the search URL for an index."""
    if index is not None:
        return ELASTICSEARCH + '/' + index + '/_search'
    return ELASTICSEARCH + '/_search'


def count_url_for(index=None):
    """Generate the search URL for an index."""
    if index is not None:
        return ELASTICSEARCH + '/' + index + '/_count'
    return ELASTICSEARCH + '/_count'


def get_json(url, data):
    """Wrap calls to requests to handle exceptions."""
    exceptions = (requests.exceptions.HTTPError,
                  requests.exceptions.ConnectionError)
    try:
        r = requests.get(url, data=data)
        r.raise_for_status()
    except exceptions as e:
        status_err(str(e))

    return r.json()


def get_count_for_querystring(query, index=None):
    """Retrieve the number of hits for a query."""
    url = count_url_for(index)
    data = json_querystring({'query': query})
    json = get_json(url, data)
    return json['count']


def parse_args():
    parser = optparse.OptionParser(usage=('%prog [-h] [-H host] [-P port] '
                                          '[-q query] [-i interval] '
                                          '[-t threashold]'))
    parser.add_option('-H', '--host', action='store', dest='host',
                      default=None,
                      help=('Hostname or IP address to use to connect to '
                            'Elasticsearch'))
    parser.add_option('-P', '--port', action='store', dest='port',
                      default=ES_PORT,
                      help='Port to use to connect to Elasticsearch')
    parser.add_option('-q', '--query', action='store', dest='query',
                      default='',
                      help='Elasticsearch query string. Examples: '
                           '"loglevel:ERROR", '
                           '"message:rabbit AND loglevel:INFO".')
    parser.add_option('-i', '--interval', action='store', dest='interval',
                      default='1d',
                      help=('How far back to start search. Examples: '
                            '1d, 4h, 30m, 45s, 2w, etc.'))
    options, _ = parser.parse_args()
    if not options.query:
        print('A query must be provided.')
        parser.print_usage()
        sys.exit(1)
    return options


def configure(options):
    global ELASTICSEARCH
    host = options.host or get_elasticsearch_bind_host()
    port = options.port
    ELASTICSEARCH = 'http://{0}:{1}'.format(host, port)


def build_query(options):
    query = options.query
    interval = options.interval

    td = None
    if interval[-1] == 'd':
        td = datetime.timedelta(days=float(interval[:-1]))
    elif interval[-1] == 'h':
        td = datetime.timedelta(hours=float(interval[:-1]))
    elif interval[-1] == 'm':
        td = datetime.timedelta(minutes=float(interval[:-1]))
    elif interval[-1] == 's':
        td = datetime.timedelta(seconds=float(interval[:-1]))
    elif interval[-1] == 'w':
        td = datetime.timedelta(weeks=float(interval[:-1]))
    if td is None:
        print('Invalid interval. Use a number followed by w (weeks), d (days) '
              'h (hours), m (minutes) or s (seconds).')
        sys.exit(1)

    now = datetime.datetime.now()
    query = '(%s) AND @timestamp:[%sZ TO %sZ]' % \
        (query, (now - td).isoformat(), now.isoformat())
    return query


def main():
    options = parse_args()
    configure(options)
    query = build_query(options)

    num_hits = get_count_for_querystring(query)

    status_ok()
    metric('HITS', 'uint32', num_hits)


if __name__ == '__main__':
    with print_output():
        main()

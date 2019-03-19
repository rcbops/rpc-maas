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

import ipaddr
from lxml import html
from maas_common import get_auth_details
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
import requests
from requests import exceptions as exc


def check(args):
    # disable warning for insecure cert on horizon
    if requests.__build__ >= 0x020400:
        requests.packages.urllib3.disable_warnings()

    splash_status_code = 0
    splash_milliseconds = 0.0
    login_status_code = 0
    login_milliseconds = 0.0

    is_up = True

    auth_details = get_auth_details()
    OS_USERNAME = auth_details['OS_USERNAME']
    OS_PASSWORD = auth_details['OS_PASSWORD']
    OS_USER_DOMAIN_NAME = auth_details['OS_USER_DOMAIN_NAME']
    HORIZON_URL = '{protocol}://{ip}'.format(
        protocol=args.protocol,
        ip=args.ip,
    )
    HORIZON_PORT = args.port

    s = requests.Session()

    try:
        r = s.get('%s:%s' % (HORIZON_URL, HORIZON_PORT),
                  verify=False,
                  timeout=180)
    except (exc.ConnectionError,
            exc.HTTPError,
            exc.Timeout) as e:
        is_up = False
        metric_bool('client_success', False, m_name='maas_horizon')
    else:
        if not (r.ok and
                re.search(args.site_name_regexp, r.content, re.IGNORECASE)):
            metric_bool('client_success', False, m_name='maas_horizon')
            status_err('could not load login page', m_name='maas_horizon')
        else:
            metric_bool('client_success', True, m_name='maas_horizon')
        splash_status_code = r.status_code
        splash_milliseconds = r.elapsed.total_seconds() * 1000

        parsed_html = html.fromstring(r.content)
        csrf_token = parsed_html.xpath(
            '//input[@name="csrfmiddlewaretoken"]/@value')[0]
        region = parsed_html.xpath(
            '//input[@name="region"]/@value')[0]
        domain = parsed_html.xpath('//input[@name="domain"]')
        s.headers.update(
            {'Content-type': 'application/x-www-form-urlencoded',
                'Referer': HORIZON_URL})
        payload = {'username': OS_USERNAME,
                   'password': OS_PASSWORD,
                   'csrfmiddlewaretoken': csrf_token,
                   'region': region}
        if domain:
            payload['domain'] = OS_USER_DOMAIN_NAME
        try:
            login_url = ('%s:%s/auth/login/') % (HORIZON_URL, HORIZON_PORT)
            if args.deploy_osp:
                login_url = ('%s:%s/dashboard/auth/login/') % (HORIZON_URL,
                                                               HORIZON_PORT)
            login_resp = s.post(login_url, data=payload, verify=False)
        except (exc.ConnectionError,
                exc.HTTPError,
                exc.Timeout) as e:
            status_err('While logging in: %s' % e, m_name='maas_horizon')

        search_phrase = 'overview'
        if args.deploy_osp:
            search_phrase = 'project'
        if not (login_resp.ok and re.search(search_phrase,
                                            login_resp.content,
                                            re.IGNORECASE)):
            status_err('could not log in', m_name='maas_horizon')

        login_status_code = login_resp.status_code
        login_milliseconds = login_resp.elapsed.total_seconds() * 1000

    status_ok(m_name='maas_horizon')
    metric_bool('horizon_local_status', is_up, m_name='maas_horizon')

    if is_up:
        metric('splash_status_code', 'uint32', splash_status_code, 'http_code')
        metric('splash_milliseconds', 'double', splash_milliseconds, 'ms')
        metric('login_status_code', 'uint32', login_status_code, 'http_code')
        metric('login_milliseconds', 'double', login_milliseconds, 'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check horizon dashboard')
    parser.add_argument('ip',
                        type=ipaddr.IPv4Address,
                        help='horizon dashboard IP address')
    parser.add_argument('site_name_regexp',
                        type=str,
                        default='openstack dashboard',
                        help='Horizon Site Name')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        action='store',
                        default='443',
                        help='Port to use for the local horizon service')
    parser.add_argument('--protocol',
                        action='store',
                        default='https',
                        help='Protocol for the local horizon service')
    # add deploy_osp arg
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        '--' + 'deploy_osp', nargs='?', default=False, const=True,
        type=bool)
    group.add_argument('--no' + 'deploy_osp', dest='deploy_osp',
                       action='store_false')

    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)

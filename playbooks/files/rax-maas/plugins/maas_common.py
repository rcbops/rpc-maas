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
from __future__ import print_function

import contextlib
import errno
import logging
import os
import pickle
import platform
import re
import sys
import traceback

from keystoneauth1.exceptions import MissingRequiredOptions
from monitorstack.common import formatters
from openstack import connect
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

AUTH_DETAILS = {'OS_USERNAME': None,
                'OS_PASSWORD': None,
                'OS_AUTH_URL': None,
                'OS_USER_DOMAIN_NAME': 'Default',
                'OS_PROJECT_DOMAIN_NAME': 'Default',
                'OS_PROJECT_NAME': 'admin',
                'OS_ENDPOINT_TYPE': 'PublicURL',
                'OS_IDENTITY_API_VERSION': None,
                'OS_API_INSECURE': True,
                'OS_VOLUME_API_VERSION': 1,
                'OS_IMAGE_API_VERSION': 1}

if 'Ubuntu' in platform.linux_distribution()[0]:
    AUTH_DETAILS.update({
        'OS_USER_DOMAIN_NAME': None,
        'OS_PROJECT_DOMAIN_NAME': None,
        'OS_PROJECT_NAME': None,
        'OS_AUTH_VERSION': None,
        'OS_TENANT_NAME': None,
        'OS_ENDPOINT_TYPE': None,
        'OS_API_INSECURE': True,
        'OS_REGION_NAME': 'RegionOne'
    })


# Disabling insecure requests warnings in case OS_API_INSECURE is set:
if AUTH_DETAILS.get('OS_API_INSECURE') is True:
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

OPENRC = '/root/openrc'
STACKRC = '/home/stack/stackrc'
PICKLE_FILE = '/root/.auth_ref.pkl'


NEUTRON_AGENT_TYPE_LIST = [
    'neutron-linuxbridge-agent',
    'neutron-dhcp-agent',
    'neutron-l3-agent',
    'neutron-metadata-agent',
    'neutron-metering-agent'
]
NOVA_SERVICE_TYPE_LIST = [
    'nova-cert',
    'nova-compute',
    'nova-conductor',
    'nova-consoleauth',
    'nova-scheduler'
]


def build_sdk_connection():
    """
    This function will create a universal connection to OpenStack with
    the OpenStack SDK. It will use the defined configuration from
    /root/.config/openstack/clouds.yaml deployed during
    maas-agent-setup.yml. It will then attempt to load pre-existing
    credentials into a session. If no credentials are found on disk,
    the the connection will re-authenticate to OpenStack automatically
    and pickle the authentication data to disk.
    """

    if os.path.exists(OPENRC) or os.path.exists(STACKRC):
        try:
            sdk_conn = connect(cloud='default', verify=False)
        except MissingRequiredOptions as e:
            raise e

        # Load pre-existing credentials and validate
        get_sdk_credentials(sdk_conn)

    return sdk_conn


def get_sdk_credentials(sdk_conn):
    """
    Load, validate, and dump credentials for the OpenStack SDK
    connection.

    The connection object uses a password adapter, so if the session
    token loaded is expired, it will obtain a valid token automatically.
    """

    try:
        sdk_conn.session
        if os.stat(PICKLE_FILE):
            with open(PICKLE_FILE, "rb") as f:
                sdk_auth_ref = pickle.load(f)

            if sdk_auth_ref:
                sdk_conn.session.auth.auth_ref = sdk_auth_ref
                token = sdk_auth_ref._auth_token
        else:
            sdk_auth_ref = None
            token = None

        validate_sdk_token(sdk_conn, sdk_auth_ref=sdk_auth_ref, token=token)
    except OSError as e:
        if e.errno == errno.ENOENT:
            validate_sdk_token(sdk_conn, sdk_auth_ref=None)
        else:
            status_err(str(e), m_name='maas_keystone')


def validate_sdk_token(sdk_conn, sdk_auth_ref=None, token=None):
    """
    Validate the existing session credentials using an inexpensive API
    call. If the token was determined to be expired, get a new one and
    dump it to PICKLE_FILE.
    """

    [i.id for i in sdk_conn.identity.services()]
    new_token = sdk_conn.identity.get_token()
    if token is not new_token or sdk_auth_ref is None:
        with open(PICKLE_FILE, 'wb') as f:
            pickle.dump(sdk_conn.session.auth.auth_ref, f)


def get_openstack_client(component):
    """Obtain an authenticated SDK client"""

    conn = build_sdk_connection()

    try:
        client = getattr(conn, component)
    except Exception as e:
        status_err(str(e))

    return client


def generate_local_endpoint(endpoint, ip, port, protocol, extend=None):
    from urlparse import urlparse

    # Remove trailing slash
    endpoint = endpoint.rstrip('/')
    url = urlparse(endpoint)
    netloc_bypass = "%s:%s" % (ip, port)
    url = url._replace(scheme=protocol)
    url = url._replace(netloc=netloc_bypass)
    url = url._replace(path=url.path + extend)
    local_endpoint = url.geturl()

    return local_endpoint


class MaaSException(Exception):
    """Base MaaS plugin exception."""


def get_auth_details(openrc_file=OPENRC):
    auth_details = AUTH_DETAILS
    pattern = re.compile(
        '^(?:export\s)?(?P<key>\w+)(?:\s+)?=(?:\s+)?(?P<value>.*)$'
    )

    try:
        with open(openrc_file) as openrc:
            for line in openrc:
                match = pattern.match(line)
                if match is None:
                    continue
                k = match.group('key')
                v = match.group('value').strip('"').strip("'")
                if k in auth_details and auth_details[k] is None:
                    auth_details[k] = v
    except IOError as e:
        if e.errno != errno.ENOENT:
            status_err(str(e), m_name='maas_keystone')
        # no openrc file, so we try the environment
        for key in auth_details.keys():
            if key in os.environ:
                auth_details[key] = os.environ.get(key)

    for key in auth_details.keys():
        if auth_details[key] is None:
            status_err('%s not set' % key, m_name='maas_keystone')

    # NOTE(cloudnull): The password variable maybe double quoted, to
    #                  fix this we strip away any extra quotes in
    #                  the variable.
    pw = auth_details['OS_PASSWORD']
    if pw.startswith("'") and pw.endswith("'"):
        pw = pw.strip("'")
    elif pw.startswith('"') and pw.endswith('"'):
        pw = pw.strip('"')
    auth_details['OS_PASSWORD'] = pw

    return auth_details


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


def status_err_no_exit(message=None, force_print=False,
                       exception=None, m_name=None):
    _telegraf_metric_name(m_name=m_name)
    if exception:
        # a status message cannot exceed 256 characters
        # 'error ' plus up to 250 from the end of the exception
        message = message[-250:]
    status('error', message, force_print=force_print)
    if exception:
        raise exception


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

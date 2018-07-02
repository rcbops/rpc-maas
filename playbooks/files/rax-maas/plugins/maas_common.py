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
import datetime
import errno
import json
import logging
import os
import re
import sys
import traceback

from monitorstack.common import formatters


AUTH_DETAILS = {'OS_USERNAME': None,
                'OS_PASSWORD': None,
                'OS_TENANT_NAME': None,
                'OS_AUTH_URL': None,
                'OS_USER_DOMAIN_NAME': None,
                'OS_PROJECT_DOMAIN_NAME': None,
                'OS_PROJECT_NAME': None,
                'OS_IDENTITY_API_VERSION': None,
                'OS_AUTH_VERSION': None,
                'OS_ENDPOINT_TYPE': None,
                'OS_API_INSECURE': True,
                'OS_REGION_NAME': 'RegionOne'}


# IMPORTANT:
# v2 keystone auth is still necessary until RPCR switches over to v3 auth


OPENRC = '/root/openrc'
TOKEN_FILE = '/root/.auth_ref.json'


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


try:
    from cinderclient import client as c_client
    from cinderclient import exceptions as c_exc

except ImportError:
    def get_cinder_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_cinder')
        status_err('Cannot import cinderclient', m_name='maas_cinder')
else:

    def get_cinder_client(previous_tries=0):
        if previous_tries > 3:
            return None
        # right now, cinderclient does not accept a previously derived token
        # or endpoint url. So we have to pass it creds and let it do it's own
        # auth each time it's called.

        auth_details = get_auth_details()
        cinder = c_client.Client('2',
                                 auth_details['OS_USERNAME'],
                                 auth_details['OS_PASSWORD'],
                                 auth_details['OS_TENANT_NAME'],
                                 auth_details['OS_AUTH_URL'],
                                 insecure=auth_details['OS_API_INSECURE'],
                                 endpoint_type=auth_details[
                                     'OS_ENDPOINT_TYPE'])

        try:
            # Do something just to ensure we actually have auth'd ok
            volumes = cinder.volumes.list()
            # Exceptions are only thrown when we iterate over volumes
            [i.id for i in volumes]
        except (c_exc.Unauthorized, c_exc.AuthorizationFailure) as e:
            cinder = get_cinder_client(previous_tries + 1)
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_cinder')
            status_err(str(e), m_name='maas_cinder')

        return cinder

try:
    import glanceclient as g_client
    from glanceclient import exc as g_exc
except ImportError:
    def get_glance_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_glance')
        status_err('Cannot import glanceclient', m_name='maas_glance')
else:
    def get_glance_client(token=None, endpoint=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)

        if not token:
            token = keystone.auth_token
        if not endpoint:
            endpoint = get_endpoint_url_for_service('image',
                                                    auth_ref,
                                                    get_endpoint_type(
                                                        auth_details))

        glance = g_client.Client('1', endpoint=endpoint, token=token)

        try:
            # We don't want to be pulling massive lists of images every time we
            # run
            image = glance.images.list(limit=1)
            # Exceptions are only thrown when we iterate over image
            [i.id for i in image]
        except g_exc.HTTPUnauthorized:
            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)
            token = keystone.auth_token

            glance = get_glance_client(token, endpoint, previous_tries + 1)
        # we only want to pass HTTPException back to the calling poller
        # since this encapsulates all of our actual API failures. Other
        # exceptions will be treated as script/environmental issues and
        # sent to status_err
        except g_exc.HTTPException:
            raise
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_glance')
            status_err(str(e), m_name='maas_glance')

        return glance

try:
    from novaclient import client as nova_client
    from novaclient.client import exceptions as nova_exc
except ImportError:
    def get_nova_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_nova')
        status_err('Cannot import novaclient', m_name='maas_nova')
else:
    def get_nova_client(auth_token=None, bypass_url=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)

        if not auth_token:
            auth_token = keystone.auth_token
        if not bypass_url:
            bypass_url = get_endpoint_url_for_service('compute',
                                                      auth_ref,
                                                      get_endpoint_type(
                                                          auth_details))

        nova = nova_client.Client('2',
                                  auth_token=auth_token,
                                  auth_url=auth_details['OS_AUTH_URL'],
                                  bypass_url=bypass_url,
                                  insecure=auth_details['OS_API_INSECURE'])

        try:
            flavors = nova.flavors.list()
            # Exceptions are only thrown when we try and do something
            [flavor.id for flavor in flavors]

        except (nova_exc.Unauthorized, nova_exc.AuthorizationFailure,
                AttributeError) as e:
            # NOTE(mancdaz)nova doesn't properly pass back unauth errors, but
            # in fact tries to re-auth, all by itself. But we didn't pass it
            # an auth_url, so it bombs out horribly with an error.

            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)
            auth_token = keystone.auth_token

            nova = get_nova_client(auth_token, bypass_url, previous_tries + 1)

            # we only want to pass ClientException back to the calling poller
            # since this encapsulates all of our actual API failures. Other
            # exceptions will be treated as script/environmental issues and
            # sent to status_err
        except nova_exc.ClientException:
            raise
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_nova')
            status_err(str(e), m_name='maas_nova')

        return nova


try:
    from keystoneclient import exceptions as k_exc
    from keystoneclient.v2_0 import client as k2_client
    from keystoneclient.v3 import client as k3_client
except ImportError:
    def keystone_auth(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_keystone')
        status_err('Cannot import keystoneclient', m_name='maas_keystone')

    def get_keystone_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_keystone')
        status_err('Cannot import keystoneclient', m_name='maas_keystone')
else:
    def keystone_auth(auth_details):
        keystone = None
        # NOTE(cloudnull): The password variable maybe double quoted, to
        #                  fix this we strip away any extra quotes in
        #                  the variable.
        pw = auth_details['OS_PASSWORD'].strip('"').strip("'")
        auth_details['OS_PASSWORD'] = pw
        try:
            if (auth_details['OS_IDENTITY_API_VERSION'] == 3 or
                    auth_details['OS_AUTH_URL'].endswith('v3')):
                keystone = k3_client.Client(
                    username=auth_details['OS_USERNAME'],
                    password=auth_details['OS_PASSWORD'],
                    user_domain_name=auth_details.get(
                        'OS_USER_DOMAIN_NAME',
                        'Default'
                    ),
                    project_domain_name=auth_details.get(
                        'OS_PROJECT_DOMAIN_NAME',
                        'Default'
                    ),
                    project_name=auth_details.get(
                        'OS_PROJECT_NAME',
                        'admin'
                    ),
                    auth_url=auth_details['OS_AUTH_URL'],
                    region_name=auth_details['OS_REGION_NAME']
                )
            else:
                keystone = k2_client.Client(
                    username=auth_details['OS_USERNAME'],
                    password=auth_details['OS_PASSWORD'],
                    tenant_name=auth_details['OS_TENANT_NAME'],
                    auth_url=auth_details['OS_AUTH_URL'],
                    region_name=auth_details['OS_REGION_NAME']
                )
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_keystone')
            status_err(str(e), m_name='maas_keystone')
        else:
            if keystone:
                return keystone.auth_ref
            else:
                raise k_exc.AuthorizationFailure()
        finally:
            try:
                if keystone:
                    with open(TOKEN_FILE, 'w') as token_file:
                        json.dump(keystone.auth_ref, token_file)
            except IOError:
                # if we can't write the file we go on
                pass

    def get_keystone_client(auth_ref=None, endpoint=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        if not auth_ref:
            auth_ref = get_auth_ref()

        auth_version = auth_ref['version']
        if not endpoint:
            endpoint = get_endpoint_url_for_service('identity', auth_ref,
                                                    'admin')
        if auth_version == 'v3':
            k_client = k3_client
            if not endpoint.endswith('v3'):
                endpoint = '%s/v3' % endpoint
        else:
            k_client = k2_client
        keystone = k_client.Client(auth_ref=auth_ref,
                                   endpoint=endpoint,
                                   insecure=AUTH_DETAILS['OS_API_INSECURE'])

        try:
            # This should be a rather light-weight call that validates we're
            # actually connected/authenticated.
            keystone.services.list()
        except (k_exc.AuthorizationFailure, k_exc.Unauthorized):
            # Force an update of auth_ref
            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref,
                                           endpoint,
                                           previous_tries + 1)
        except (k_exc.HttpServerError, k_exc.ClientException) as e:
            metric_bool('client_success', False, m_name='maas_keystone')
            status_err(str(e), m_name='maas_keystone')
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_keystone')
            status_err(str(e), m_name='maas_keystone')

        return keystone


try:
    from neutronclient.common import exceptions as n_exc
    from neutronclient.neutron import client as n_client
except ImportError:
    def get_neutron_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_neutron')
        status_err('Cannot import neutronclient', m_name='maas_neutron')
else:
    def get_neutron_client(token=None, endpoint_url=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)

        if not token:
            token = keystone.auth_token
        if not endpoint_url:
            endpoint_url = get_endpoint_url_for_service('network',
                                                        auth_ref,
                                                        get_endpoint_type(
                                                            auth_details))

        neutron = n_client.Client('2.0',
                                  token=token,
                                  endpoint_url=endpoint_url,
                                  insecure=auth_details['OS_API_INSECURE'])

        try:
            # some arbitrary command that should always have at least 1 result
            agents = neutron.list_agents()
            # iterate the list to ensure we actually have something
            [i['id'] for i in agents['agents']]

        # if we have provided a bum token, neutron wants to try and reauth
        # itself but it can't as we didn't provide it an auth_url and all that
        # jazz. Since we want to auth again ourselves (so we can update our
        # local token) we'll just catch the exception it throws and move on
        except n_exc.NoAuthURLProvided:
            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)
            token = keystone.auth_token

            neutron = get_neutron_client(token, endpoint_url,
                                         previous_tries + 1)

        # we only want to pass NeutronClientException back to the caller
        # since this encapsulates all of our actual API failures. Other
        # exceptions will be treated as script/environmental issues and
        # sent to status_err
        except n_exc.NeutronClientException as e:
            raise
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_neutron')
            status_err(str(e), m_name='maas_neutron')

        return neutron


try:
    from heatclient import client as heat_client
    from heatclient import exc as h_exc
except ImportError:
    def get_heat_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_heat')
        status_err('Cannot import heatclient', m_name='maas_heat')
else:
    def get_heat_client(token=None, endpoint=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)

        if not token:
            token = keystone.auth_token
        if not endpoint:
            endpoint = get_endpoint_url_for_service('orchestration',
                                                    auth_ref,
                                                    get_endpoint_type(
                                                        auth_details))

        heat = heat_client.Client('1',
                                  endpoint=endpoint,
                                  token=token,
                                  insecure=auth_details['OS_API_INSECURE'])
        try:
            heat.build_info.build_info()
        except h_exc.HTTPUnauthorized:
            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)

            token = keystone.auth_token
            heat = get_heat_client(token, endpoint, previous_tries + 1)
        except h_exc.HTTPException:
            raise
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_heat')
            status_err(str(e), m_name='maas_heat')

        return heat


try:
    from ironicclient import client as ironic_client
    from ironicclient import exc as ironic_exc
except ImportError:
    def get_ironic_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_ironic')
        status_err('Cannot import ironicclient', m_name='maas_ironic')
else:
    def get_ironic_client(token=None, endpoint=None, previous_tries=0):
        if previous_tries > 3:
            return None

        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)
        if not token:
            token = keystone.auth_token
        if not endpoint:
            endpoint = get_endpoint_url_for_service('baremetal',
                                                    auth_ref,
                                                    get_endpoint_type(
                                                        auth_details))

        ironic = ironic_client.get_client(
            '1', os_auth_token=token,
            ironic_url=endpoint,
            insecure=auth_details['OS_API_INSECURE'])

        try:
            nodes = ironic.node.list()
            [node.uuid for node in nodes]

        except (ironic_exc.Unauthorized, ironic_exc.AuthorizationFailure,
                AttributeError) as e:

            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)
            token = keystone.auth_token

            ironic = get_ironic_client(token, endpoint, previous_tries + 1)

            # we only want to pass ClientException back to the calling poller
            # since this encapsulates all of our actual API failures. Other
            # exceptions will be treated as script/environmental issues and
            # sent to status_err
        except ironic_exc.ClientException:
            raise
        except Exception as e:
            status_err(str(e))

        return ironic


try:
    from magnumclient import client as magnum_client
    from magnumclient.common.apiclient import exceptions as magnum_exc
except ImportError:
    def get_magnum_client(*args, **kwargs):
        metric_bool('client_success', False, m_name='maas_magnum')
        status_err('Cannot import magnumclient', m_name='maas_magnum')
else:
    def get_magnum_client(token=None, endpoint=None, previous_tries=0):
        if previous_tries > 3:
            return None

        # first try to use auth details from auth_ref so we
        # don't need to auth with keystone every time
        auth_ref = get_auth_ref()
        auth_details = get_auth_details()
        keystone = get_keystone_client(auth_ref)

        if not token:
            token = keystone.auth_token
        if not endpoint:
            endpoint = get_endpoint_url_for_service('container-infra',
                                                    auth_ref,
                                                    get_endpoint_type(
                                                        auth_details))

        magnum = magnum_client.Client('1',
                                      endpoint_override=endpoint,
                                      auth_token=token,
                                      insecure=auth_details['OS_API_INSECURE'])
        try:
            magnum.cluster_templates.list()
        except h_exc.HTTPUnauthorized:
            auth_ref = force_reauth()
            keystone = get_keystone_client(auth_ref)

            token = keystone.auth_token
            magnum = get_magnum_client(token, endpoint, previous_tries + 1)
        except magnum_exc.HttpError:
            raise
        except Exception as e:
            metric_bool('client_success', False, m_name='maas_magnum')
            status_err(str(e), m_name='maas_magnum')

        return magnum


class MaaSException(Exception):
    """Base MaaS plugin exception."""


def is_token_expired(token, auth_details):
    for fmt in ('%Y-%m-%dT%H:%M:%SZ', '%Y-%m-%dT%H:%M:%S.%fZ'):
        try:
            if auth_details['OS_AUTH_URL'].endswith('v3'):
                expires_at = token.get('expires_at')
            else:
                expires_at = token['token'].get('expires')

            expires = datetime.datetime.strptime(expires_at, fmt)
            break
        except ValueError as e:
            pass
    else:
        raise e
    return datetime.datetime.now() >= expires


def get_service_catalog(auth_ref):
    return auth_ref.get('catalog',
                        # Default back to Keystone v2.0's auth-ref format
                        auth_ref.get('serviceCatalog'))


def get_endpoint_type(auth_details):
    endpoint_type = auth_details['OS_ENDPOINT_TYPE']
    if endpoint_type == 'publicURL':
        return 'public'
    if endpoint_type == 'adminURL':
        return 'admin'
    return 'internal'


def get_auth_ref():
    auth_details = get_auth_details()
    auth_ref = get_auth_from_file()
    if auth_ref is None:
        auth_ref = keystone_auth(auth_details)

    if is_token_expired(auth_ref, auth_details):
        auth_ref = keystone_auth(auth_details)

    return auth_ref


def get_auth_from_file():
    try:
        with open(TOKEN_FILE) as token_file:
            auth_ref = json.load(token_file)

        return auth_ref
    except IOError as e:
        if e.errno == errno.ENOENT:
            return None
        status_err(str(e), m_name='maas_keystone')


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
                v = match.group('value')
                if k in auth_details and auth_details[k] is None:
                    auth_details[k] = v
    except IOError as e:
        if e.errno != errno.ENOENT:
            status_err(str(e), m_name='maas_keystone')
        # no openrc file, so we try the environment
        for key in auth_details.keys():
            auth_details[key] = os.environ.get(key)

    for key in auth_details.keys():
        if auth_details[key] is None:
            status_err('%s not set' % key, m_name='maas_keystone')

    return auth_details


def get_url_for_type(endpoint, url_type, auth_version):
    # TURTLES-694: in kilo environments, we need to avoid v2.0 URLs, otherwise
    # MaaS will 404 when it tries to check openstack services. in only this
    # circumstance, we suggest a different URL; otherwise, for backward
    # compatibility, we give two different endpoint keys a try
    if auth_version == 'v3' and 'v2.0' in endpoint.get('url', ''):
        return None
    return endpoint.get('url', endpoint.get(url_type + 'URL'))


def get_endpoint_url_for_service(service_type, auth_ref,
                                 url_type='public', version=None):
    # version = the version identifier on the end of the url. eg:
    # for keystone admin api v3:
    # http://172.29.236.3:35357/v3
    # so you'd pass version='v3'
    service_catalog = get_service_catalog(auth_ref)
    auth_version = auth_ref['version']

    for service in service_catalog:
        if service['type'] == service_type:
            for endpoint in service['endpoints']:
                url = get_url_for_type(endpoint, url_type, auth_version)
                if url is not None:
                    # If version is not provided or it is provided and the url
                    # ends with it, we want to return it, otherwise we want to
                    # do nothing.
                    if not version or url.endswith(version):
                        return url


def force_reauth():
    auth_details = get_auth_details()
    return keystone_auth(auth_details)


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

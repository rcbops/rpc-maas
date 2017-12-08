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

import urlparse

from monitorstack import utils
from monitorstack.utils import os_utils as ost

import monitorstack_creds

from maas_metric_common import *


class Struct(object):
    def __init__(self, items):
        self.__dict__.update(items)


class OSClient(object):
    def __init__(self):
        pass

    @property
    def ost_conn(self):
        creds = utils.read_config('/root/monitorstack.ini')['ALL']
        return ost.OpenStack(os_auth_args=creds)

    def _session_req(self, endpoint_url, path):
        """Return compute resource limits for a project.

        :param path: URL path to make a request against.
        :type path: str
        :param interface: Interface name, normally [internal, public, admin].
        :type interface: str
        :returns: dict
        """
        if not endpoint_url.endswith('/'):
            endpoint_url = '%s/' % endpoint_url
        sess_url = urlparse.urljoin(endpoint_url, path)
        return self.ost_conn.conn.session.get(sess_url).json()

    def _glance_list_images(self, endpoint=None):
        """Return a list images."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='images'
            )
            items = list()
            for item in sess_items['images']:
                items.append(
                    self.ost_conn.conn.image.get_image(item['id'])
                )
            return items
        else:
            return self.ost_conn.conn.image.images()

    def glance_shim(self, endpoint=None):
        """Return a pusedo glance client object.

        The glance shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class glance(object):
            class images(object):
                @staticmethod
                def list(search_opts=None):
                    """Return a list of images.

                    NOTE(cloudnull): search_opts is only defined for legacy
                                     compatibility.
                    """
                    items = list()
                    for item in self._glance_list_images(endpoint):
                        items.append(item)
                    return items
        return glance

    def _heat_list_stacks(self, endpoint=None):
        """Return a list of stacks."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='stacks'
            )
            items = list()
            for item in sess_items['stacks']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.orchestration.stacks()

    def heat_shim(self, endpoint=None):
        """Return a pusedo heat client object.

        The heat shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class heat(object):
            class build_info(object):
                @staticmethod
                def build_info():
                    items = list()
                    for item in self._heat_list_stacks(endpoint):
                        items.append(item)
                    return items
        return heat

    def _ironic_list_nodes(self, endpoint=None):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='nodes'
            )
            items = list()
            for item in sess_items['nodes']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.bare_metal.nodes()

    def ironic_shim(self, endpoint=None):
        """Return a pusedo ironic client object.

        The ironic shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class ironic(object):
            class node(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._ironic_list_nodes(endpoint):
                        items.append(item)
                    return items
        return ironic

    def _keystone_list_services(self, endpoint=None):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='services'
            )
            items = list()
            for item in sess_items['services']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.identity.services()

    def _keystone_list_projects(self, endpoint=None):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='projects'
            )
            items = list()
            for item in sess_items['projects']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.identity.projects()

    def _keystone_list_users(self, endpoint=None):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='users'
            )
            items = list()
            for item in sess_items['users']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.identity.users()

    def keystone_shim(self, endpoint=None):
        """Return a pusedo ironic client object.

        The ironic shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class keystone(object):
            class services(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._keystone_list_services(endpoint):
                        items.append(item)
                    return items

            class tenants(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._keystone_list_projects(endpoint):
                        items.append(item)
                    return items

            class projects(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._keystone_list_projects(endpoint):
                        items.append(item)
                    return items

            class users(object):
                @staticmethod
                def list(domain=None):
                    """Return a list users.

                    NOTE(cloudnull): domain is only defined for legacy
                                     compatibility.
                    """
                    items = list()
                    for item in self._keystone_list_users(endpoint):
                        items.append(item)
                    return items
        return keystone

    def _magnum_list(self, endpoint=None, list_type=None):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='v1/%s' % list_type
            )
        else:
            identity = self.ost_conn.conn.identity
            services = identity.services()
            endpoints = identity.endpoints()
            for service in services:
                if service.type.lower() == 'container-infra':
                    for endpoint in endpoints:
                        if endpoint.service_id == service.id:
                            if endpoint.interface.lower() == 'internal':
                                endpoint_data = identity.get_endpoint(endpoint)
                                sess_items = self._session_req(
                                    endpoint_url=endpoint_data.url,
                                    path='v1/%s' % list_type
                                )
            else:
                raise SystemExit('No magnum endpoint found.')

        items = list()
        for item in sess_items[list_type]:
            items.append(Struct(item))
        return items

    def magnum_shim(self, endpoint=None):
        """Return a pusedo magnum client object.

        The magnum shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class magnum(object):
            class cluster_templates(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._magnum_list(endpoint,
                                                  list_type='mservices'):
                        items.append(item)
                    return items
            class mservices(object):
                @staticmethod
                def list():
                    items = list()
                    for item in self._magnum_list(endpoint,
                                                  list_type='clustertemplates'):
                        items.append(item)
                    return items
        return magnum

    def _neutron_list_agents(self, endpoint):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='v2.0/agents'
            )
            items = list()
            for item in sess_items['agents']:
                items.append(item)
            return items
        else:
            return self.ost_conn.conn.network.agents()

    def _neutron_list_networks(self, endpoint):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='v2.0/networks'
            )
            items = list()
            for item in sess_items['networks']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.network.networks()

    def _neutron_list_routers(self, endpoint):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='v2.0/routers'
            )
            items = list()
            for item in sess_items['routers']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.network.routers()

    def _neutron_list_subnets(self, endpoint):
        """Return a list of nodes."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='v2.0/subnets'
            )
            print(sess_items)
            items = list()
            for item in sess_items['subnets']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.network.subnets()

    def neutron_shim(self, endpoint=None):
        """Return a pusedo neutron client object.

        The neutron shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        class neutron(object):
            @staticmethod
            def list_agents(host=None):
                return {'agents': list(self._neutron_list_agents(endpoint))}
            @staticmethod
            def list_networks():
                return {'networks': list(self._neutron_list_networks(endpoint))}
            @staticmethod
            def list_routers():
                return {'routers': list(self._neutron_list_routers(endpoint))}
            @staticmethod
            def list_subnets():
                return {'subnets': list(self._neutron_list_subnets(endpoint))}
        return neutron

    def _nova_list_servers(self, endpoint=None, tenant_id=None):
        """Return a list servers."""
        if endpoint:
            endpoint = endpoint.format(tenant_id=tenant_id)
            if not endpoint.endswith(tenant_id):
                if not endpoint.endswith('/'):
                    endpoint = '%s/' % endpoint
                endpoint = urlparse.urljoin(endpoint, tenant_id)

            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='servers'
            )
            items = list()
            for item in sess_items['servers']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.compute.servers()

    def _nova_list_services(self, endpoint=None):
        """Return a list servers."""
        if endpoint:
            sess_items = self._session_req(
                endpoint_url=endpoint,
                path='os-services'
            )
            items = list()
            for item in sess_items['services']:
                items.append(Struct(item))
            return items
        else:
            return self.ost_conn.conn.compute.servers()

    def nova_shim(self, endpoint=None):
        """Return a pusedo glance client object.

        The nova shim is a nested set of classes which fake the old client
        syntax. When all calls to the top level function can be removed or
        cleaned up this shim should be removed as well.
        """
        project = self.ost_conn.conn.identity.find_project('admin')
        tenant_id = project.id

        class nova(object):
            class services(object):
                @staticmethod
                def list(search_opts=None, host=None):
                    """Return a list servers.

                    NOTE(cloudnull): search_opts is only defined for legacy
                                     compatibility.
                    """
                    items = list()
                    for item in self._nova_list_services(endpoint):
                        items.append(item)
                    return items

            class servers(object):
                @staticmethod
                def list(search_opts=None, host=None):
                    """Return a list servers.

                    NOTE(cloudnull): search_opts is only defined for legacy
                                     compatibility.
                    """
                    items = list()
                    for item in self._nova_list_servers(endpoint, tenant_id):
                        items.append(item)
                    return items
        return nova


def get_auth_details():
    """Return a dict of authentication credentials."""
    return monitorstack_creds.get_auth_details()


def get_auth_ref():
    """Return an authentication object in dict form."""
    _ost = OSClient()
    _ref = _ost.ost_conn.conn.authenticator.get_auth_ref(
        session=_ost.ost_conn.conn.session
    )
    auth_ref = dict()
    auth_ref['auth_token'] = _ref.auth_token
    auth_ref['expires_at'] = _ref.expires
    auth_ref['version'] = _ref.version
    auth_ref['project_id'] = auth_ref['tenant_id'] = _ref.project_id
    return auth_ref


def get_endpoint_url_for_service(service_type, auth_ref, interface):
    """Return the endpoint URL for a given service.

    NOTE(cloudnull): The "auth_ref" key is only here for legacy purposes. This
                     should be removed when the octavia plugins can be updated.
    """
    _ost = OSClient()
    return _ost.ost_conn.conn.session.get_endpoint(
        interface=interface,
        service_type=service_type
    )


def get_glance_client(endpoint=None):
    """Return a psuedo client objcet."""
    _ost = OSClient()
    return _ost.glance_shim(endpoint=endpoint)


def get_heat_client(endpoint=None):
    """Return a psuedo client objcet."""
    _ost = OSClient()
    return _ost.heat_shim(endpoint=endpoint)


def get_ironic_client(endpoint=None):
    """Return a psuedo client objcet."""
    _ost = OSClient()
    return _ost.ironic_shim(endpoint=endpoint)


def get_keystone_client(endpoint=None, auth_ref=None):
    """Return a keystone object.

    NOTE(cloudnull): The "auth_ref" key is only here for legacy purposes. This
                     should be removed when the octavia plugins can be updated.
    """
    _ost = OSClient()
    keystone = _ost.keystone_shim(endpoint=endpoint)
    for k, v in get_auth_ref().items():
        setattr(keystone, k, v)
    return keystone


def get_magnum_client(endpoint=None):
    """Return a psuedo client objcet."""
    _ost = OSClient()
    return _ost.ironic_shim(endpoint=endpoint)


def get_neutron_client(endpoint_url=None):
    """Return a psuedo client objcet.

    NOTE(cloudnull): The "endpoint_url" key is different for legacy purposes.
                     This should be set to "endpoint" when the neutron plugins
                     can be updated.
    """
    _ost = OSClient()
    return _ost.neutron_shim(endpoint=endpoint_url)


def get_nova_client(bypass_url=None, auth_token=None):
    """Return a psuedo client objcet.

    NOTE(cloudnull): The "bypass_url" key is different for legacy purposes.
                     This should be set to "endpoint" when the neutron plugins
                     can be updated.
    NOTE(cloudnull): The "auth_token" is provided only for legacy purposes.
                     When we can update the nova checks this should be removed.
    """
    _ost = OSClient()
    return _ost.nova_shim(endpoint=bypass_url)

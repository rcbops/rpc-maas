#!/usr/bin/env python
# Copyright 2019, Rackspace US, Inc.
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

from socket import gaierror, gethostbyname
from urlparse import urlparse

from ansible.module_utils.basic import AnsibleModule  # noqa: ignore=H303
from keystoneauth1.exceptions import MissingRequiredOptions
import netaddr
from openstack import connect


DOCUMENTATION = """
---
module: service_discovery
short_description:
    - Discovery module for MaaS that uses the OpenStack service catalog.
description:
    - This module utilizes an OpenStack SDK connection to obtain the service
      catalog and create a set of facts based on the endpoint data.
options:
    raxdc:
        description:
            - A boolean identifying whether the deployment is in a Rackspace
              data center (RDC) or customer data center (CDC).
        required: true
    internal_vip:
        description:
            - An IP address identifying the internal OpenStack VIP.
        required: true
    external_vip:
        description:
            - An IP address identifying the external OpenStack VIP.
        required: true
author:
    - Nathan Pawelek (@npawelek)
"""

EXAMPLES = """
- name: Service discovery
  service_discovery:
    raxdc: False
    internal_vip: 172.29.236.100
    external_vip: 172.99.120.153
"""


class ServiceDiscovery(object):
    def __init__(self, module):
        self.module = module
        self.raxdc = module.params.get('raxdc')
        self.internal_vip = module.params.get('internal_vip')
        self.external_vip = module.params.get('external_vip')
        self.conn = self.build_sdk_connection()
        self.catalog_details = dict()
        self.cert_expiry = False
        self.cert_expiry_list = list(dict())
        self.pnm = False
        self.api_endpoints = dict()
        self.maas_external_hostname = ''
        self.maas_external_ip_address = ''
        self.use_public = False
        self.cinder_backends = {
            "local": list(),
            "shared": list()
        }

    def build_sdk_connection(self):
        """
        Create a universal connection to OpenStack with the OpenStack SDK.
        It will use the defined configuration from
        /root/.config/openstack/clouds.yaml.
        """

        try:
            sdk_conn = connect(cloud='default', verify=False)
        except MissingRequiredOptions as e:
            message = ('Missing option in clouds.yaml: %s' % str(e))
            self.module.fail_json(msg=message)
        else:
            return sdk_conn

    def parse_service_catalog(self):
        """
        Parse the OpenStack service catalog and identify service components.
        """

        try:
            catalog = self.conn.service_catalog

            items = ['protocol', 'port', 'address']
            invalid_chars = '-_'
            for service in catalog:
                # NOTE(npawelek): Sanitize the service catalog name to remove
                # dashes and underscores
                service_name = service['name']
                for c in invalid_chars:
                    service_name = service_name.replace(c, '')
                for endpoint in service['endpoints']:
                    url = urlparse(endpoint.get('url'))
                    for item in items:
                        key_name = "%s_%s_%s" % (
                            service_name,
                            endpoint['interface'],
                            item)
                        if item == 'protocol':
                            self.catalog_details[key_name] = str(url.scheme)
                        elif item == 'port':
                            self.parse_port(key_name, url)
                        else:
                            self.catalog_details[key_name] = str(
                                url.netloc.split(':')[0])

        except Exception as e:
            message = ('Issue parsing the service catalog. The following'
                       'error was received: %s' % str(e))
            self.module.fail_json(msg=message)

    def parse_port(self, key, url):
        """
        Identify endpoint port. If a port is not detected in the url, this
        attempts to use the protocol to associate a valid port.
        """

        if not url.port:
            if url.scheme == 'https':
                self.catalog_details[key] = 443
            elif url.scheme == 'http':
                self.catalog_details[key] = 80
            else:
                raise Exception('Endpoint object has an unexpected port and'
                                'scheme: %s' % url)
        else:
            self.catalog_details[key] = url.port

    def generate_facts(self):
        """
        Gather information based on data center (raxdc or cdc) and endpoint
        validation. This results in whether PNM should be enabled, a list
        of certificates to validate expiry on, and the associated endpoint
        targets for private or public pollers.

        It's assumed that RDC deployments are accessible from public Rackspace
        Monitoring pollers, so we only check the public interface first. If
        PNM is required, then iterate over internal interfaces.
        """

        if self.raxdc:
            self.validate_endpoints(['public'])
            if self.pnm:
                self.validate_endpoints(['internal'])
        else:
            self.validate_endpoints(['public', 'internal'])

            # No CDC private endpoints found. Must validate public endpoints.
            if len(self.api_endpoints) == 0:
                self.use_public = True
                self.validate_endpoints(['public', 'internal'],
                                        use_public=self.use_public)

        # Set generic fallback vip depending on PNM
        if self.pnm and self.use_public is False:
            if self.internal_vip.replace('.', '').isdigit():
                self.maas_external_hostname = self.internal_vip
                self.maas_external_ip_address = self.internal_vip
            else:
                vip_ip = self.get_url_ip_address(self.internal_vip)
                self.maas_external_hostname = self.internal_vip
                self.maas_external_ip_address = vip_ip
        else:
            if self.external_vip.replace('.', '').isdigit():
                self.maas_external_hostname = self.external_vip
                self.maas_external_ip_address = self.external_vip
            else:
                vip_ip = self.get_url_ip_address(self.external_vip)
                self.maas_external_hostname = self.external_vip
                self.maas_external_ip_address = vip_ip

    def validate_endpoints(self, interface_list, use_public=False):
        """
        Determine whether the endpoint is natively usable or requires
        additional overrides for the target URL and IP. This will run against
        both presented interfaces to detect values usable for both
        lb_api_checks and private_lb_api_checks.
        """
        for interface in interface_list:

            # Only use address keys from catalog (netloc)
            string = "_%s_address" % interface

            # Walk the service catalog
            for key, value in self.catalog_details.items():
                if string in key:
                    # Detect IP address or hostname
                    if value.replace('.', '').isdigit():
                        is_private = self.validate_private_ip(value)

                        if is_private is False and self.raxdc is False:
                            if use_public is True:
                                self.pnm = True
                                self.service_specific_overrides(key, value)
                            else:
                                pass
                        elif is_private:
                            self.pnm = True
                            self.service_specific_overrides(key, value)

                        else:
                            self.service_specific_overrides(key, value)

                    else:
                        # Ensure the hostname is resolvable by the system
                        url_ip = self.get_url_ip_address(value)

                        # Validation for SSL cert expiry
                        self.cert_expiry_check(key, value, url_ip)

                        # Determine if the URL is private
                        is_private = self.validate_private_ip(url_ip)

                        # CDC environments should always have PNM enabled.
                        # Skip if public endpoints have public addresses
                        # which likely aren't accessible from PNM poller
                        if is_private is False and self.raxdc is False:
                            if use_public is True:
                                self.pnm = True
                                self.service_specific_overrides(key,
                                                                value,
                                                                url_ip)
                            else:
                                pass

                        # Enable PNM and configure associated api facts
                        elif is_private:
                            self.pnm = True
                            self.service_specific_overrides(key, value, url_ip)

                        # Configure api facts for public pollers
                        else:
                            self.service_specific_overrides(key, value, url_ip)

    def get_url_ip_address(self, url):
        """Ensure the hostname is resolvable by the system"""
        try:
            url_ip = gethostbyname(url)
            return url_ip
        except gaierror as e:
            message = ('%s does not appear to be resolvable '
                       'by DNS. Ensure the address is '
                       'resolvable or add an entry to '
                       '/etc/hosts on all controller nodes. '
                       'PNM Exception: %s') % (url, str(e))
            self.module.fail_json(msg=message)
        except Exception as e:
            message = 'Failed to get URL ip address for %s. Error: %s' % (
                url, str(e))
            self.module.fail_json(msg=message)

    def cert_expiry_check(self, key, url, url_ip):
        """
        Enable the certificate expiry check and create a unique list of
        endpoints for validating all certificates.
        """

        endpoint = "%s_%s" % (key.split('_')[0], key.split('_')[1])
        protocol_key = "%s_protocol" % endpoint

        # Ensure protocol is https
        if self.catalog_details[protocol_key] == 'https':
            self.cert_expiry = True

            # Determine if the URL (excluding port) is already in the cert list
            url_check = len(
                [i for i in self.cert_expiry_list if url in i.get('cert_url',
                                                                  '')]
            )

            if url_check == 0:
                port_key = "%s_port" % endpoint
                cert_url = "https://%s:%s/" % (url,
                                               self.catalog_details[port_key])
                cert_dict = {
                    "cert_url": cert_url,
                    "cert_ip": url_ip
                }
                self.cert_expiry_list.append(cert_dict)

    def validate_private_ip(self, address):
        """
        Determine whether the associated IP address is valid and is an
        RFC 1918 private address (non-routable).
        """

        try:
            ipaddr = netaddr.IPAddress(address)

        except netaddr.AddrFormatError as e:
            message = ('%s is not a proper IP address according to '
                       'netaddr. PNM Exception: %s') % (address, str(e))
            self.module.fail_json(msg=message)

        except Exception as e:
            message = 'Unable to validate IP %s. Error: %s' % (address, str(e))
            self.module.fail_json(msg=message)

        else:
            if ipaddr.is_private():
                return True
            else:
                return False

    def service_specific_overrides(self, key, value, url_ip=None):
        items = ['url', 'ip']
        endpoint = "%s_%s" % (key.split('_')[0], key.split('_')[1])

        for item in items:
            key_name = "%s_%s" % (endpoint, item)
            if item == 'url':
                self.set_full_address(key_name, value)
            else:
                if url_ip is None:
                    self.api_endpoints[key_name] = value
                else:
                    self.api_endpoints[key_name] = url_ip

    def set_full_address(self, key, address):
        """
        Defines the full address of a specific endpoint. proto://address:port
        """

        endpoint = "%s_%s" % (key.split('_')[0], key.split('_')[1])

        for attr in 'protocol', 'port':
            attr_key = "%s_%s" % (endpoint, attr)
            if attr == 'protocol':
                protocol = self.catalog_details[attr_key]
            else:
                port = self.catalog_details[attr_key]

        self.api_endpoints[key] = "%s://%s:%s/" % (protocol, address, port)

    def get_cinder_backends(self):
        """Discovers hosts for local and/or shared block storage backend pools.

        Queries the OpenStack Block Storage API to identify all backend
        pools. Using the volume backend name (everything after #), hosts
        are split into local and/or shared volume backends. This will
        provide dynamic cinder-volume hosts for any nomenclature.

        Returns:
            A dict mapping of volume hosts within local and/or shared backends.
            For example:

            {
                'local': [
                    'infra02@midtier',
                    'infra01@midtier',
                    'infra03@midtier',
                    'infra03@ceph',
                    'infra01@ceph',
                    'infra02@ceph'
                ],
                'shared': []
            }
        """
        cinder = self.conn.block_storage

        backend_pools = [str(bp.name) for bp in cinder.backend_pools()]
        backend_names = [i.split('#')[-1] for i in backend_pools]
        unique_backend_names = set(backend_names)
        unique_backend_counts = dict()

        for name in unique_backend_names:
            unique_backend_counts[name] = backend_names.count(name)

        for pool in backend_pools:
            host, backend_name = pool.split('#')

            if unique_backend_counts[backend_name] == 1:
                self.cinder_backends['shared'].append(host)
            else:
                self.cinder_backends['local'].append(host)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            raxdc=dict(required=True, type='bool'),
            internal_vip=dict(required=True),
            external_vip=dict(required=True)
        ),
        supports_check_mode=False
    )

    discovery = ServiceDiscovery(module)
    discovery.parse_service_catalog()
    discovery.generate_facts()
    discovery.get_cinder_backends()

    module.exit_json(
        changed=False,
        ansible_facts={
            'cert_expiry': discovery.cert_expiry,
            'cert_expiry_list': discovery.cert_expiry_list,
            'pnm': discovery.pnm,
            'api_endpoints': discovery.api_endpoints,
            'maas_external_hostname': discovery.maas_external_hostname,
            'maas_external_ip_address': discovery.maas_external_ip_address,
            'maas_cinder_local_backends': discovery.cinder_backends['local'],
            'maas_cinder_shared_backends': discovery.cinder_backends['shared']
        }
    )


if __name__ == '__main__':
    main()

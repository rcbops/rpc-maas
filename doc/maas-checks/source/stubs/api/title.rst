The API category contains `remote.http
<https://developer.rackspace.com/docs/rackspace-monitoring/v1/tech-ref-info/check-type-reference/#remote-http>`_
checks and alarms for all supported OpenStack service endpoints. The
checks are deployed to the ``shared-infra_hosts`` inventory group and
are only enabled on the first node of the inventory group. The
``maas-sdk-integration.yml`` playbook uses the Service Catalog for
automatic provisioning of target URLs of service endpoints. This allows
endpoints to contain non-standard hostnames and ports, and still
function out-of-the-box. Depending on whether the endpoint resides
within a Rackspace data center or uses RFC 1918 address space, the
service-specific ``lb_api_check_*`` or ``private_lb_api_check_*``
template is deployed. These use public and private pollers respectively
and query the service endpoints to determine a valid response metrics.

=======================
Configuration Reference
=======================

These playbooks allow deployers to monitor clouds using Rackspace Monitoring
as a Service. The playbooks can be used with OpenStack-Ansible or on their
own using Ansible static inventory.

Default variables
~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/main.yml
   :language: yaml
   :start-after: under the License.


Agent playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-agent.yml
   :language: yaml
   :start-after: under the License.

Container playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-container.yml
   :language: yaml
   :start-after: under the License.

Host playbook variables
~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-host.yml
   :language: yaml
   :start-after: under the License.

Infra playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-infra.yml
   :language: yaml
   :start-after: under the License.

OpenStack playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-openstack.yml
   :language: yaml
   :start-after: under the License.

Hummingbird playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-hummingbird.yml
   :language: yaml
   :start-after: under the License.

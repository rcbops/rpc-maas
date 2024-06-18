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

.. literalinclude:: ../../playbooks/vars/maas.yml
   :language: yaml
   :start-after: under the License.

Ubuntu related playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-ubuntu.yml
   :language: yaml
   :start-after: under the License.

RedHat related playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-redhat.yml
   :language: yaml
   :start-after: under the License.

OpenStack playbook variables
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-openstack.yml
   :language: yaml
   :start-after: under the License.

Ceph playbook variables
~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: ../../playbooks/vars/maas-ceph.yml
   :language: yaml
   :start-after: Descriptions pulled

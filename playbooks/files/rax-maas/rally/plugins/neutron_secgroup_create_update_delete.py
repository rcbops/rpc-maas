from rally.task import validation

from rally_openstack.common import consts
from rally_openstack.task import scenario
from rally_openstack.task.scenarios.neutron import utils

@validation.add("required_services",
                services=[consts.Service.NEUTRON])
@validation.add("required_platform", platform="openstack", users=True)
@scenario.configure(context={"cleanup@openstack": ["neutron"]},
                    name=("NeutronSecurityGroup"
                          ".create_update_and_delete_security_groups"))
class CreateUpdateAndDeleteSecurityGroups(utils.NeutronScenario):

    def run(self, security_group_create_args=None,
            security_group_update_args=None):
        """Create and update Neutron security-groups.

        Measure the "neutron security-group-create" and "neutron
        security-group-update" command performance.

        :param security_group_create_args: dict, POST /v2.0/security-groups
                                           request options
        :param security_group_update_args: dict, PUT /v2.0/security-groups
                                           update options
        """
        security_group_create_args = security_group_create_args or {}
        security_group_update_args = security_group_update_args or {}
        security_group = self._create_security_group(
            **security_group_create_args)
        self._update_security_group(security_group,
                                    **security_group_update_args)
        self._delete_security_group(security_group)

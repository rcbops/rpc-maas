import tempfile

from rally.task import validation

from rally_openstack.common import consts
from rally_openstack.task import scenario
from rally_openstack.task.scenarios.swift import utils


"""Scenarios for Swift Objects."""

@validation.add("required_services", services=[consts.Service.SWIFT])
@validation.add("required_platform", platform="openstack", users=True)
@scenario.configure(context={"cleanup@openstack": ["swift"]},
                    name="SwiftObjects.create_c_and_o"
                         "_then_download_and_delete_all")
class CreateContainerAndObjectThenDownloadAndDeleteAll(utils.SwiftScenario):

    def run(self, object_size=1024, **kwargs):
        container_name = None
        container_name = self._create_container(**kwargs)

        with tempfile.TemporaryFile() as dummy_file:
            dummy_file.truncate(object_size)
            dummy_file.seek(0)
            object_name = self._upload_object(container_name, dummy_file)[1]

        self._download_object(container_name, object_name)
        self._delete_object(container_name, object_name)
        self._delete_container(container_name)

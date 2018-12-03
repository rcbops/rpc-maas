#!/usr/bin/env bash

# Copyright 2018, Rackspace US, Inc.
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

## Shell Opts ----------------------------------------------------------------

set -exu

echo "Run Maas tests on an OSP13 Multi Node AIO (MNAIO)"

# set up command wrapper and host entry
export MNAIO_DIRECTOR='ssh -ttt -oStrictHostKeyChecking=no 192.168.24.2'
echo "192.168.24.2 director" >> /etc/hosts

export WORKING_DIR="${WORKING_DIR:-$(pwd)}"
echo "Current directory: ${WORKING_DIR}"

# sync maas repo to director node and prep for configs
echo "+---------------- Syncing Maas code to director --------------+"
rsync -av ${WORKING_DIR}/ director:/opt/rpc-maas/ && echo "Done."
set -xe
echo "+---------------- HOST RELEASE AND KERNEL --------------+"
lsb_release -a
uname -a
echo "+---------------- MNAIO RELEASE AND KERNEL --------------+"
${MNAIO_DIRECTOR} <<EOC
  set -xe
  echo "+--------------- DIRECTOR RELEASE AND KERNEL --------------+"
  lsb_release -a
  uname -a
  echo "+--------------- DIRECTOR RELEASE AND KERNEL --------------+"
  cd /opt/rpc-maas/
  ls -la
  echo "+--------------- END OF DIRECTOR PREVIEW --------------+"
EOC

# start the osp rpc-maas install from director
${MNAIO_DIRECTOR} "source /opt/rpc-maas/tests/RE_ENV && /opt/rpc-maas/tests/test-ansible-functional.sh"
echo "OSP13 MNAIO Maas tests completed..."

function gate_job_exit_tasks {
  # This environment variable captures the exit code
  # which was present when the trap was initiated.
  # This would be the success/failure of the test.
  export TEST_EXIT_CODE=$?

  pushd /opt/osp-mnaio
    ansible -i playbooks/inventory/hosts deploy_hosts -m shell -a "subscription-manager unregister"
  popd
}

# Set gate job exit traps, this is run regardless of exit state when the job finishes.
trap gate_job_exit_tasks EXIT
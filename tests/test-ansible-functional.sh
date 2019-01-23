#!/usr/bin/env bash

# Copyright 2016, Rackspace US, Inc.
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

# WARNING:
# This file is use by all OpenStack-Ansible roles for testing purposes.
# Any changes here will affect all OpenStack-Ansible role repositories
# with immediate effect.

# PURPOSE:
# This script executes a test Ansible playbook for the purpose of
# functionally testing the role. It supports a convergence test,
# check mode and an idempotence test.

## Shell Opts ----------------------------------------------------------------

set -exuo pipefail

echo "Run Functional Tests"
echo "+-------------------- FUNCTIONAL ENV VARS --------------------+"
env
echo "+-------------------- FUNCTIONAL ENV VARS --------------------+"

## Vars ----------------------------------------------------------------------

export RE_JOB_SCENARIO="${RE_JOB_SCENARIO:-master}"
export RE_JOB_ACTION="${RE_JOB_ACTION:-deploy}"
export TESTING_HOME="${TESTING_HOME:-$HOME}"
export WORKING_DIR="${WORKING_DIR:-$(pwd)}"
export ROLE_NAME="${ROLE_NAME:-''}"

export ANSIBLE_CALLBACK_WHITELIST="profile_tasks"
export ANSIBLE_OVERRIDES="${ANSIBLE_OVERRIDES:-false}"
export ANSIBLE_PARAMETERS="${ANSIBLE_PARAMETERS:-false}"
export ANSIBLE_LOG_DIR="${TESTING_HOME}/.ansible/logs"
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-functional.log"

if [ ${RE_JOB_SCENARIO} = osp13 ]; then
  # Env vars prep for osp 13
  export ANSIBLE_HOST_KEY_CHECKING="false"
  export WORKING_DIR="/opt/rpc-maas"
  # Set ansible version for embeded ansible runtime
  export ANSIBLE_INVENTORY="${ANSIBLE_INVENTORY:-false}"
else
  # Ansible Inventory will be set to OSA
  export ANSIBLE_INVENTORY="${ANSIBLE_INVENTORY:-/opt/openstack-ansible/playbooks/inventory}"
  if [ "${RE_JOB_SCENARIO}" == "queens" ]; then
    export ANSIBLE_INVENTORY="/opt/openstack-ansible/inventory"
  fi
fi

# NOTE: Create an artifact to make a unique entity for queens+ gates. This is required
# as OSA now sets the hostname generically as 'aio1' which will cause affected
# gates to use the same entity
# This will automatically work for new gates
case $RE_JOB_SCENARIO in
  ceph|hummingbird|kilo|liberty|mitaka|newton|ocata|pike)
    echo "There is no need to set maas_fqdn_extension on ${RE_JOB_SCENARIO}"
    echo | tee /tmp/maas_fqdn_extension
    ;;
  *)
    echo "Create a 16 character unique string to set as maas_fqdn_extension"
    echo $(< /dev/urandom tr -dc '[:alnum:]' | head -c${1:-16} | sed 's/^/./') | tee /tmp/maas_fqdn_extension
    ;;
esac

# The maas_rally performance monitoring requires a modern (>1.9) version of
# ansible that is not available in liberty and mitaka.  There is no reason
# to run it in a ceph context either.
case $RE_JOB_SCENARIO in
  kilo|liberty|mitaka|ceph|hummingbird|osp13|rocky)
    export TEST_PLAYBOOK="${TEST_PLAYBOOK:-$WORKING_DIR/tests/test.yml}"
    ;;
  *)
    export TEST_PLAYBOOK="${TEST_PLAYBOOK:-$WORKING_DIR/tests/test_with_maas_rally.yml}"
    ;;
esac

export TEST_SETUP_PLAYBOOK="${TEST_SETUP_PLAYBOOK:-$WORKING_DIR/tests/test-setup.yml}"
export TEST_CLEANUP_PLAYBOOK="${TEST_CLEANUP_PLAYBOOK:-$WORKING_DIR/playbooks/maas-raxmon-delete-resources.yml}"
export TEST_CHECK_MODE="${TEST_CHECK_MODE:-false}"
export TEST_IDEMPOTENCE="${TEST_IDEMPOTENCE:-false}"

export COMMON_TESTS_PATH="${COMMON_TESTS_PATH:-$WORKING_DIR/tests/common}"

echo "ANSIBLE_OVERRIDES: ${ANSIBLE_OVERRIDES}"
echo "ANSIBLE_PARAMETERS: ${ANSIBLE_PARAMETERS}"
echo "TEST_SETUP_PLAYBOOK: ${TEST_SETUP_PLAYBOOK}"
echo "TEST_CLEANUP_PLAYBOOK: ${TEST_CLEANUP_PLAYBOOK}"
echo "TEST_PLAYBOOK: ${TEST_PLAYBOOK}"
echo "TEST_CHECK_MODE: ${TEST_CHECK_MODE}"
echo "TEST_IDEMPOTENCE: ${TEST_IDEMPOTENCE}"

## Functions -----------------------------------------------------------------

function set_ansible_parameters {
  # NOTE(tonytan4ever): We always skip preflight metadata check
  TEST_DEFAULTS="-f 10 -e maas_pre_flight_metadata_check_enabled=false -e create_entity_if_not_exists=true -e cleanup_entity=true"
  ANSIBLE_CLI_PARAMETERS="${TEST_DEFAULTS:-${ANSIBLE_OVERRIDE_CLI_PARAMETERS}}"

  if [ "${ANSIBLE_PARAMETERS}" != false ]; then
    ANSIBLE_CLI_PARAMETERS+=" ${ANSIBLE_PARAMETERS}"
  fi

  if [ -f "${ANSIBLE_OVERRIDES}" ]; then
    ANSIBLE_CLI_PARAMETERS+=" -e @${ANSIBLE_OVERRIDES}"
  fi

  if [ -d "/etc/openstack_deploy" ]; then
    ANSIBLE_CLI_PARAMETERS+=" $(for i in $(ls /etc/openstack_deploy/user_*.yml); do echo -ne "-e @$i "; done)"
  fi
}

function setup_embedded_ansible {
  # Installation of embedded ansible for rpc-maas
  if [[ ! -d "/opt/magnanimous-turbo-chainsaw" ]]; then
    export ANSIBLE_VERSION=2.6.5
<<<<<<< HEAD
    curl https://raw.githubusercontent.com/rcbops/magnanimous-turbo-chainsaw/master/scripts/setup.sh | bash
  fi
  pushd /opt/magnanimous-turbo-chainsaw/scripts
    PS1="${PS1:-'\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '}" ANSIBLE_VERSION=2.6.5 source /opt/magnanimous-turbo-chainsaw/scripts/setup-workspace.sh
  popd
  export ANSIBLE_EMBED_BINARY="${ANSIBLE_EMBED_HOME}/bin/ansible-playbook -e \$USER_VARS"
=======
    curl -s https://raw.githubusercontent.com/rcbops/magnanimous-turbo-chainsaw/master/scripts/setup.sh | bash
  fi
  PS1="${PS1:-'\[\033[01;31m\]\h\[\033[01;34m\] \W \$\[\033[00m\] '}" ANSIBLE_VERSION=2.6.5 source /opt/magnanimous-turbo-chainsaw/scripts/setup-workspace.sh
  export ANSIBLE_EMBED_BINARY="${ANSIBLE_EMBED_HOME}/bin/ansible-playbook -e \$USER_ALL_VARS"
>>>>>>> Update for more rocky and embedded ansible changes
  export ANSIBLE_BINARY="${ANSIBLE_BINARY:-$ANSIBLE_EMBED_BINARY}"

  if [ ${RE_JOB_SCENARIO} = osp13 ]; then
    ANSIBLE_BINARY+=" -i ${WORKING_DIR}/inventory/rpcr_dynamic_inventory.py"
  fi
}

function execute_ansible_playbook {
  # Ansible task runner
  setup_embedded_ansible
  set_ansible_parameters
  CMD_TO_EXECUTE="${ANSIBLE_BINARY} $@ ${ANSIBLE_CLI_PARAMETERS}"
  echo "Executing: ${CMD_TO_EXECUTE}"
  echo "With:"
  echo "    ANSIBLE_INVENTORY: ${ANSIBLE_INVENTORY}"
  echo "    ANSIBLE_LOG_PATH: ${ANSIBLE_LOG_PATH}"

  ${CMD_TO_EXECUTE}
  deactivate
}

function gate_job_exit_tasks {
  # This environment variable captures the exit code
  # which was present when the trap was initiated.
  # This would be the success/failure of the test.
  export TEST_EXIT_CODE=$?

  # Cleanup gating entities and agent tokens
  execute_ansible_playbook ${TEST_CLEANUP_PLAYBOOK}
}

function pin_environment {
  # NOTE(cloudnull): Earlier versions of OSA depended on an ansible.cfg file to lock-in
  #                  plugins and other configurations. This does the same thing using
  #                  environment variables.
  . "$WORKING_DIR/tests/ansible-env.rc"
}

function ensure_osa_dir {
  # NOTE(cloudnull): Create the configuration dirs if not already present
  if [[ ! -d "/etc/openstack_deploy" ]]; then
    mkdir -p "/etc/openstack_deploy"
  fi
  if [[ ! -d "/etc/openstack_deploy/env.d" ]]; then
    mkdir -p "/etc/openstack_deploy/env.d"
  fi
  if [[ ! -d "/etc/openstack_deploy/conf.d" ]]; then
    mkdir -p "/etc/openstack_deploy/conf.d"
  fi
  if [[ "${RE_JOB_SCENARIO}" == "osp13" && ! -f "/etc/openstack_deploy/user_rpcm_${RE_JOB_SCENARIO}_vars.yml" ]]; then
    echo -e "---\ndeploy_osp: true" > /etc/openstack_deploy/user_rpcm_${RE_JOB_SCENARIO}_vars.yml
  fi
}

function install_director_dev_packages {
  get_pip
  yum install -y python-virtualenv iptables python-devel
  yum groupinstall -y "Development Tools"
}

function get_pip {
  # Use pip opts to add options to the pip install command.
  # This can be used to tell it which index to use, etc.
  PIP_OPTS=${PIP_OPTS:-""}

  # The python executable to use when executing get-pip is passed
  # as a parameter to this function.
  GETPIP_PYTHON_EXEC_PATH="${1:-$(which python)}"

  # Download the get-pip script using the primary or secondary URL
  GETPIP_CMD="curl --silent --show-error --retry 5"
  GETPIP_FILE="/opt/get-pip.py"
  # If GET_PIP_URL is set, then just use it
  if [ -n "${GET_PIP_URL:-}" ]; then
    ${GETPIP_CMD} ${GET_PIP_URL} > ${GETPIP_FILE}
  else
    # Otherwise, try the two standard URL's
    ${GETPIP_CMD} https://bootstrap.pypa.io/get-pip.py > ${GETPIP_FILE}\
      || ${GETPIP_CMD} https://raw.githubusercontent.com/pypa/get-pip/master/get-pip.py > ${GETPIP_FILE}
  fi

  ${GETPIP_PYTHON_EXEC_PATH} ${GETPIP_FILE} ${PIP_OPTS} \
     pip --upgrade
}

function enable_maas_api {
  # NOTE(cloudnull): Enable the maas api by setting the "maas_use_api" option to true.
  #                  This will also pull a token from RAX MaaS and set it as an env var.
  ensure_osa_dir
  get_pip

  echo "Show the version of the pip packages in the functional venv."
  echo "This helps identify issues with pyrax"
  echo "START PACKAGE LIST"
  pip list --format=columns || pip list
  /usr/bin/env python -c 'import sys; print(sys.path)'
  echo "END PACKAGE LIST"

  PYTHON_BIN="$(which python)"
  pip install -U virtualenv --isolated
  virtualenv --no-setuptools --python="${PYTHON_BIN}" /opt/test-maas
  /opt/test-maas/bin/pip install setuptools requests --isolated --upgrade --force-reinstall

  # NOTE(tonytan4ever):  pip on newton will broken because of a mis-installed version of setuptools
  if [ "${RE_JOB_SCENARIO}" == "newton" ]; then
    /opt/test-maas/bin/pip install setuptools==30.1.0 --upgrade --isolated --force-reinstall
  fi

  # Collect a maas auth token for API tests
  /opt/test-maas/bin/python $WORKING_DIR/tests/maasutils.py --username "${PUBCLOUD_USERNAME}" \
                                                            --apikey "${PUBCLOUD_API_KEY}"

  # We're sourcing the file so that it's not written to a collected artifact
  . ~/maas-vars.rc

  # Write out the varuable file
  cat > /etc/openstack_deploy/user_rpcm_use_api_variables.yml <<EOF
---
# Enable the API usage
maas_use_api: true

# Set the default notification plan, in the gate this is set here
maas_notification_plan: npTechnicalContactsEmail

# Use the previously created artifact to make a unique entity for queens+ gates
# This is required as OSA now sets the hostname generically as 'aio1' which will
# cause affected gates to use the same entity
maas_fqdn_extension: "{{ lookup('file', '/tmp/maas_fqdn_extension', errors='ignore') | default('') }}"

# Set the entity name to be created
maas_entity_name: "{{ ansible_hostname }}{{ maas_fqdn_extension }}"
EOF
}

## Main ----------------------------------------------------------------------

# Set gate job exit traps, this is run regardless of exit state when the job finishes.
trap gate_job_exit_tasks EXIT

# Create /etc/openstack_deploy if not exists
ensure_osa_dir

# Export additional ansible environment variables if running Kilo or Liberty
if [ "${RE_JOB_SCENARIO}" == "kilo" ]; then
  pin_environment

elif [ "${RE_JOB_SCENARIO}" == "liberty" ]; then
  pin_environment
fi

# Ensure the log directory exists
if [[ ! -d "${ANSIBLE_LOG_DIR}" ]]; then
  mkdir -p "${ANSIBLE_LOG_DIR}"
fi

# Run test setup playbook
execute_ansible_playbook ${TEST_SETUP_PLAYBOOK}

# Enable MaaS API testing if the cloud variables are set.
if [ ! "${PUBCLOUD_USERNAME:-false}" = false ] && [ ! "${PUBCLOUD_API_KEY:-false}" = false ]; then
  if [ "${RE_JOB_SCENARIO}" = "osp13" ]; then
    install_director_dev_packages
  fi
  enable_maas_api
fi

# If the test for check mode is enabled, then execute it
if [ "${TEST_CHECK_MODE}" == "true" ]; then

  # Set the path for the output log
  export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-check.log"

  # Execute the test playbook in check mode
  execute_ansible_playbook --check ${TEST_PLAYBOOK}
fi

# Set the path for the output log
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-execute.log"

# Execute the test playbook
execute_ansible_playbook ${TEST_PLAYBOOK}

# If the idempotence test is enabled, then execute the
# playbook again and verify that nothing changed/failed
# in the output log.
if [ "${TEST_IDEMPOTENCE}" == "true" ]; then

  # Set the path for the output log
  export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-idempotence.log"

  # Execute the test playbook
  execute_ansible_playbook ${TEST_PLAYBOOK}

  # Check the output log for changed/failed tasks
  if grep -q "changed=0.*failed=0" ${ANSIBLE_LOG_PATH}; then
    echo "Idempotence test: pass"
  else
    echo "Idempotence test: fail"
    exit 1
  fi
fi

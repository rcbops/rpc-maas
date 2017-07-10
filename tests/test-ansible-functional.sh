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

set -eovu

echo "Run Functional Tests"
echo "+-------------------- FUNCTIONAL ENV VARS --------------------+"
env
echo "+-------------------- FUNCTIONAL ENV VARS --------------------+"

## Vars ----------------------------------------------------------------------

export IRR_CONTEXT="${IRR_CONTEXT:-master}"
export TESTING_HOME="${TESTING_HOME:-$HOME}"
export WORKING_DIR="${WORKING_DIR:-$(pwd)}"
export ROLE_NAME="${ROLE_NAME:-''}"

export ANSIBLE_CALLBACK_WHITELIST="profile_tasks"
export ANSIBLE_OVERRIDES="${ANSIBLE_OVERRIDES:-$WORKING_DIR/tests/$ROLE_NAME-overrides.yml}"
export ANSIBLE_PARAMETERS="${ANSIBLE_PARAMETERS:-false}"
export ANSIBLE_LOG_DIR="${TESTING_HOME}/.ansible/logs"
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-functional.log"
# Ansible Inventory will be set to OSA
export ANSIBLE_INVENTORY="/opt/openstack-ansible/playbooks/inventory"

export TEST_PLAYBOOK="${TEST_PLAYBOOK:-$WORKING_DIR/tests/test.yml}"
export TEST_SETUP_PLAYBOOK="${TEST_SETUP_PLAYBOOK:-$WORKING_DIR/tests/test-setup.yml}"
export TEST_CHECK_MODE="${TEST_CHECK_MODE:-false}"
export TEST_IDEMPOTENCE="${TEST_IDEMPOTENCE:-false}"

export COMMON_TESTS_PATH="${WORKING_DIR}/tests/common"

echo "ANSIBLE_OVERRIDES: ${ANSIBLE_OVERRIDES}"
echo "ANSIBLE_PARAMETERS: ${ANSIBLE_PARAMETERS}"
echo "TEST_SETUP_PLAYBOOK: ${TEST_SETUP_PLAYBOOK}"
echo "TEST_PLAYBOOK: ${TEST_PLAYBOOK}"
echo "TEST_CHECK_MODE: ${TEST_CHECK_MODE}"
echo "TEST_IDEMPOTENCE: ${TEST_IDEMPOTENCE}"

## Functions -----------------------------------------------------------------

function set_ansible_parameters {
  ANSIBLE_CLI_PARAMETERS=""

  if [ "${ANSIBLE_PARAMETERS}" != false ]; then
    ANSIBLE_CLI_PARAMETERS+=" ${ANSIBLE_PARAMETERS}"
  fi

  if [ -f "${ANSIBLE_OVERRIDES}" ]; then
    ANSIBLE_CLI_PARAMETERS+=" -e @${ANSIBLE_OVERRIDES}"
  fi
}

function execute_ansible_playbook {

  CMD_TO_EXECUTE="openstack-ansible $@ ${ANSIBLE_CLI_PARAMETERS}"
  echo "Executing: ${CMD_TO_EXECUTE}"
  echo "With:"
  echo "    ANSIBLE_INVENTORY: ${ANSIBLE_INVENTORY}"
  echo "    ANSIBLE_LOG_PATH: ${ANSIBLE_LOG_PATH}"

  ${CMD_TO_EXECUTE}

}

function gate_job_exit_tasks {
  source "${COMMON_TESTS_PATH}/test-log-collect.sh"
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
}

function influx_pin_environment {
  # NOTE(cloudnull): Create log_host to influx_hosts environmental link.
  ensure_osa_dir

  cat > "/etc/openstack_deploy/env.d/rpcm_influx_hosts.yml" <<EOF
---
component_skel:
  influx:
    belongs_to:
      - influx_all
      - influx_hosts

container_skel:
  influx_container:
    belongs_to:
      - log_containers
    contains:
      - influx
    properties:
      is_metal: true
EOF
}

function enable_maas_api {
  # NOTE(cloudnull): Enable the maas api by setting the "maas_use_api" option to true.
  #                  This will also pull a token from RAX MaaS and set it as an env var.
  ensure_osa_dir

  echo "Show the version of the pip packages in the functional venv."
  echo "This helps identify issues with pyrax"
  echo "START PACKAGE LIST"
  pip list --format=columns || pip list
  echo "END PACKAGE LIST"

  # Collect a maas auth token for API tests
  $WORKING_DIR/tests/maasutils.py --username "${PUBCLOUD_USERNAME}" \
                                  --api-key "${PUBCLOUD_API_KEY}" get_token_url

  # We're sourcing the file so that it's not written to a collected artifact
  . ~/maas-vars.rc

  # Write out the varuable file
  cat > /etc/openstack_deploy/user_rpcm_use_api_variables.yml <<EOF
---
# Enable the API usage
maas_use_api: true

# Will restart the agent service ONLY once at the end of a site.yml run
maas_restart_independent: false

# Set the default notification plan, in the gate this is set here
maas_notification_plan: npTechnicalContactsEmail
EOF
}

## Main ----------------------------------------------------------------------

# Set gate job exit traps, this is run regardless of exit state when the job finishes.
trap gate_job_exit_tasks EXIT

# Enable MaaS API testing if the cloud variables are set.
if [ ! "${PUBCLOUD_USERNAME:-false}" = false ] && [ ! "${PUBCLOUD_API_KEY:-false}" = false ]; then
  enable_maas_api
fi

# Link the log_hosts of OSA to influx_hosts
influx_pin_environment

# Export additional ansible environment variables if running Kilo or Liberty
if [ "${IRR_CONTEXT}" == "kilo" ]; then
  pin_environment

elif [ "${IRR_CONTEXT}" == "liberty" ]; then
  pin_environment
fi

# Ensure the log directory exists
if [[ ! -d "${ANSIBLE_LOG_DIR}" ]]; then
  mkdir -p "${ANSIBLE_LOG_DIR}"
fi

# Prepare the extra CLI parameters used in each execution
set_ansible_parameters

# Run test setup playbook
execute_ansible_playbook ${TEST_SETUP_PLAYBOOK}

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
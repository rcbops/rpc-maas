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
set -eovu

## Vars ----------------------------------------------------------------------
export RE_JOB_SCENARIO="${RE_JOB_SCENARIO:-master}"
export RE_JOB_ACTION="${RE_JOB_ACTION:-deploy}"
export TESTING_HOME="${TESTING_HOME:-$HOME}"
export TEST_DIR="$(readlink -f $(dirname ${0}))"
export ANSIBLE_LOG_DIR="${TESTING_HOME}/.ansible/logs"
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-local-test-aio.log"
export ANSIBLE_OVERRIDE_CLI_PARAMETERS='-e create_entity_if_not_exists=false -e cleanup_entity=false'

export OSA_TESTS_CHECKOUT="b146d649e675d748a58af238c7b37138b8194f1f"
export OSA_REQUIREMENTS_CHECKOUT="master"
export UPPER_CONSTRAINTS_FILE="https://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?h=${OSA_REQUIREMENTS_CHECKOUT:-master}"
export OSA_TEST_DEPS="https://git.openstack.org/cgit/openstack/openstack-ansible-tests/plain/test-ansible-deps.txt?h=${OSA_TESTS_CHECKOUT:-master}"

if [ "${RE_JOB_SCENARIO}" = "osp13" ]; then
  > ${TEST_DIR}/RE_ENV
  ## TODO: Add pubcloud username/api key here
  env | grep "RE_\|PUBCLOUD_USERNAME\|PUBCLOUD_API_KEY" | while read -r match; do
  varName=$(echo ${match} | cut -d= -f1)
  echo "export ${varName}='${!varName}'" >> ${TEST_DIR}/RE_ENV
  done

  echo $'\n' > ${TEST_DIR}/RE_ENV
  echo "RE_ENV_file to set: \n"
  cat ${TEST_DIR}/RE_ENV

  exit 0
fi



## Functions -----------------------------------------------------------------
function determine_distro {
    # Determine the distribution we are running on, so that we can configure it
    # appropriately.
    source /etc/os-release 2>/dev/null
    export DISTRO_ID="${ID}"
    export DISTRO_NAME="${NAME}"
    export DISTRO_VERSION_ID="${VERSION_ID}"
}

function ssh_key_create {
  # Ensure that the ssh key exists and is an authorized_key
  key_path="${HOME}/.ssh"
  key_file="${key_path}/id_rsa"

  # Ensure that the .ssh directory exists and has the right mode
  if [ ! -d ${key_path} ]; then
    mkdir -p ${key_path}
    chmod 700 ${key_path}
  fi

  # Ensure a full keypair exists
  if [ ! -f "${key_file}" -o ! -f "${key_file}.pub" ]; then

    # Regenrate public key if private key exists
    if [ -f "${key_file}" ]; then
      ssh-keygen -f ${key_file} -y > ${key_file}.pub
    fi

    # Delete public key if private key missing
    if [ ! -f "${key_file}" ]; then
      rm -f ${key_file}.pub
    fi

    # Regenerate keypair if both keys missing
    if [ ! -f "${key_file}" -a ! -f "${key_file}.pub" ]; then
      ssh-keygen -t rsa -f ${key_file} -N ''
    fi

  fi

  # Ensure that the public key is included in the authorized_keys
  # for the default root directory and the current home directory
  key_content=$(cat "${key_file}.pub")
  if ! grep -q "${key_content}" ${key_path}/authorized_keys; then
    echo "${key_content}" | tee -a ${key_path}/authorized_keys
  fi
}

## Main ----------------------------------------------------------------------

determine_distro

ssh_key_create

case ${DISTRO_ID} in
    centos|rhel)
        $RHT_PKG_MGR -y install \
          python-virtualenv iptables python-devel
        $RHT_PKG_MGR -y groupinstall \
          "Development Tools"
        ;;
    ubuntu)
        apt-get update
        DEBIAN_FRONTEND=noninteractive apt-get -y install \
          python-virtualenv iptables util-linux apt-transport-https netbase build-essential python-dev
        ;;
    opensuse*)
        zypper -n install -l \
          python-virtualenv iptables
        # Leap ships with python3.4 which is not supported by ansible and as
        # such we are using python2
        # See https://github.com/ansible/ansible/issues/24180
        PYTHON_EXEC_PATH="/usr/bin/python2"
        ;;
esac

# Create rpc-maas venv for testing
PYTHON_BIN="$(which python)"
virtualenv --python="${PYTHON_EXEC_PATH:-${PYTHON_BIN}}" /opt/test-maas

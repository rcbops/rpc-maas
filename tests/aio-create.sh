#!/usr/bin/env bash

# Copyright 2017, Rackspace US, Inc.
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

echo "Building an AIO"
echo "+-------------------- AIO ENV VARS --------------------+"
env
echo "+-------------------- AIO ENV VARS --------------------+"

## Vars ----------------------------------------------------------------------

export RE_JOB_SCENARIO="${RE_JOB_SCENARIO:-master}"
export TESTING_HOME="${TESTING_HOME:-$HOME}"
export ANSIBLE_LOG_DIR="${TESTING_HOME}/.ansible/logs"
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-aio.log"

## Functions -----------------------------------------------------------------
function pin_jinja {
  # Pin Jinja2 because versions >2.9 is broken w/ earlier versions of Ansible.
  if ! grep -i 'jinja2' /opt/openstack-ansible/global-requirement-pins.txt; then
    echo 'Jinja2==2.8' | tee -a /opt/openstack-ansible/global-requirement-pins.txt
  else
    sed -i 's|^Jinja2.*|Jinja2==2.8|g' /opt/openstack-ansible/global-requirement-pins.txt
  fi
  sed -i 's|^Jinja2.*|Jinja2==2.8|g' /opt/openstack-ansible/requirements.txt
}

function pin_galera {
  # NOTE(cloudnull): The MariaDB repos in these releases used https, this broke the deployment.
  #                  These patches simply point at the same repos just without https.
  # Create the configuration dir if it's not present
  if [[ ! -d "/etc/openstack_deploy" ]]; then
    mkdir -p /etc/openstack_deploy
  fi

  cat > /etc/openstack_deploy/user_rpco_galera.yml <<EOF
---
galera_client_apt_repo_url: "http://mirror.rackspace.com/mariadb/repo/${1}/ubuntu"
galera_apt_repo_url: "http://mirror.rackspace.com/mariadb/repo/${1}/ubuntu"
galera_apt_percona_xtrabackup_url: "http://repo.percona.com/apt"
EOF
}

function disable_security_role {
  # NOTE(cloudnull): The security role is tested elsewhere, there's no need to run it here.
  if [[ ! -d "/etc/openstack_deploy" ]]; then
    mkdir -p /etc/openstack_deploy
  fi
  echo "apply_security_hardening: false" | tee -a /etc/openstack_deploy/user_nosec.yml
}

function enable_ironic {
  if [[ ! -d "/etc/openstack_deploy" ]]; then
    mkdir -p /etc/openstack_deploy
  fi
  echo "
  confd_overrides:
    aio:
      - name: cinder.yml.aio
      - name: glance.yml.aio
      - name: heat.yml.aio
      - name: horizon.yml.aio
      - name: keystone.yml.aio
      - name: neutron.yml.aio
      - name: nova.yml.aio
      - name: swift.yml.aio
      - name: ironic.yml.aio" | tee -a /etc/openstack_deploy/user_ironic.yml
}

function install_ovs {
  if [ ! -z ${use_ovs+x} ]; then
    sed -i 's/neutron_linuxbridge_agent/neutron_openvswitch_agent/' /opt/openstack-ansible/etc/openstack_deploy/openstack_user_config.yml.aio
    echo '
openstack_host_specific_kernel_modules:
  - name: "openvswitch"
  - pattern: "CONFIG_OPENVSWITCH"
  - group: "network_hosts"

neutron_plugin_type: ml2.ovs
neutron_ml2_drivers_type: "vlan"
neutron_provider_networks:
  - network_flat_networks: "*"
  - network_types: "vlan"
  - network_vlan_ranges: "physnet1:1:1"
  - network_mappings: "physnet1:br-provider"' | tee -a /etc/openstack_deploy/user_variables.yml
  fi
}

function add_lxc_overrides {
  if [ ! -e /etc/openstack_deploy/user_resolvconf_fix.yml ] ; then
    touch /etc/openstack_deploy/user_resolvconf_fix.yml
  fi
  echo '
lxc_cache_prep_pre_commands: "rm -f /etc/resolv.conf || true"
lxc_cache_prep_post_commands: "ln -s ../run/resolvconf/resolv.conf /etc/resolv.conf -f"' | tee -a /etc/openstack_deploy/user_resolvconf_fix.yml
}

function spice_repo_fix {
  cat > /etc/openstack_deploy/user_osa_variables_spice.yml <<EOF
---
nova_spicehtml5_git_repo: https://gitlab.freedesktop.org/spice/spice-html5
EOF
}

## Main ----------------------------------------------------------------------

echo "Gate test starting
with:
  RE_JOB_SCENARIO: ${RE_JOB_SCENARIO}
  TESTING_HOME: ${TESTING_HOME}
  ANSIBLE_LOG_PATH: ${ANSIBLE_LOG_PATH}
"

if [[ -d "${TESTING_HOME}/.ansible" ]]; then
  mv "${TESTING_HOME}/.ansible" "${TESTING_HOME}/.ansible.$(date +%M%d%H%s)"
fi

if [[ -f "${TESTING_HOME}/.ansible.cfg" ]]; then
  mv "${TESTING_HOME}/.ansible.cfg" "${TESTING_HOME}/.ansible.cfg.$(date +%M%d%H%s)"
fi

mkdir -p "${ANSIBLE_LOG_DIR}"

# NOTE(odyssey4me):
# The test execution nodes do not have these packages installed, so
# we need to do that for the OSA build to work.
apt-get install -y iptables util-linux apt-transport-https netbase

echo 'Debug::Acquire::http "true";' > /etc/apt/apt.conf.d/99debug

if [ ! -d "/opt/openstack-ansible" ]; then
  git clone https://github.com/openstack/openstack-ansible /opt/openstack-ansible
else
  pushd /opt/openstack-ansible
    git fetch --all
  popd
fi

pushd /opt/openstack-ansible
  if [ "${RE_JOB_SCENARIO}" == "kilo" ]; then
    git checkout "97e3425871659881201106d3e7fd406dc5bd8ff3"  # Last commit of Kilo
    pin_jinja
    pin_galera "5.5"
    # NOTE(cloudnull): In kilo we had a broken version of the ssh plugin listed in the role
    #                  requirements file. This patch gets the role from master and puts
    #                  into place which satisfies the role requirement.
    mkdir -p /etc/ansible/roles

  elif [ "${RE_JOB_SCENARIO}" == "liberty" ]; then
    git checkout "06d0fd344b5b06456a418745fe9937a3fbedf9b2"  # Last commit of Liberty
    pin_jinja
    pin_galera "10.0"
    # Change Affinity - only create 1 galera/rabbit/keystone/horizon and repo server for testing MaaS
    sed -i 's/\(_container\: \).*/\11/' /opt/openstack-ansible/etc/openstack_deploy/openstack_user_config.yml.aio
    spice_repo_fix

  elif [ "${RE_JOB_SCENARIO}" == "mitaka" ]; then
    git checkout "fbafe397808ef3ee3447fe8fefa6ac7e5c6ff144"  # Last commit of Mitaka
    pin_jinja
    pin_galera "10.0"
    export OA_DIR="/opt/openstack-ansible"
    export BOOTSTRAP_OPTS=${BOOTSTRAP_OPTS:-"pip_get_pip_options='-c $OA_DIR/global-requirement-pins.txt'"}
    export UPPER_CONSTRAINTS_FILE="http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?id=$(awk '/requirements_git_install_branch:/ {print $2}' playbooks/defaults/repo_packages/openstack_services.yml) -U"
    spice_repo_fix

  elif [ "${RE_JOB_SCENARIO}" == "newton" ]; then
    git remote add rcbops-fork https://github.com/rcbops/openstack-ansible.git
    git fetch --all
    git checkout -b newton-fix rcbops-fork/stable/newton
    enable_ironic
    # NOTE(tonytan4ever): newton needs this to get around gating:
    # https://rackspace.slack.com/archives/CAD5VFMHU/p1525445460000172
    add_lxc_overrides
    if [ "${RE_JOB_IMAGE}" == "trusty" ]; then
      export UPPER_CONSTRAINTS_FILE="http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?id=$(awk '/requirements_git_install_branch:/ {print $2}' playbooks/defaults/repo_packages/openstack_services.yml) -U"
    fi

  elif [ "${RE_JOB_SCENARIO}" == "ocata" ]; then
    git checkout "stable/ocata"  # Branch checkout of Ocata (Current Stable)
    enable_ironic

  elif [ "${RE_JOB_SCENARIO}" == "pike" ]; then
    git checkout "stable/pike"  # Branch checkout of Pike (Current Stable)
    enable_ironic

  else
    enable_ironic
  fi

  # Install ovs agent if applicable
  install_ovs

  # Disbale tempest on newer releases
  if [[ -f "tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2" ]]; then
    sed -i 's|^tempest_install.*|tempest_install: no|g' tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2
    sed -i 's|^tempest_run.*|tempest_run: no|g' tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2
  fi

  # Disable tempest on older releases
  sed -i '/.*run-tempest.sh.*/d' scripts/gate-check-commit.sh  # Disable the tempest run

  # NOTE(tonytan4ever): pin pip to the last working version before pip 10
  pip install -U -r /opt/openstack-ansible/global-requirement-pins.txt

  # Pin python-ldap so it stops breaking everything
  echo "python-ldap<3;python_version=='2.7'" >> /opt/openstack-ansible/global-requirement-pins.txt

  # Disable the sec role
  disable_security_role

  # Setup an AIO
  sudo -H --preserve-env ./scripts/gate-check-commit.sh

popd

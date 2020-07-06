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

set -exovu

echo "Building an AIO"
echo "+-------------------- AIO ENV VARS --------------------+"
env
echo "+-------------------- AIO ENV VARS --------------------+"

## Vars ----------------------------------------------------------------------

export RE_JOB_SCENARIO="${RE_JOB_SCENARIO:-stein}"
export TESTING_HOME="${TESTING_HOME:-$HOME}"
export ANSIBLE_LOG_DIR="${TESTING_HOME}/.ansible/logs"
export ANSIBLE_LOG_PATH="${ANSIBLE_LOG_DIR}/ansible-aio.log"

## Functions -----------------------------------------------------------------
function pin_jinja {
  # Pin Jinja2 because versions >2.9 is broken w/ earlier versions of Ansible.
  if ! grep -i 'jinja2' ${OA_DIR}/global-requirement-pins.txt; then
    echo 'Jinja2==2.8' | tee -a ${OA_DIR}/global-requirement-pins.txt
  else
    sed -i 's|^Jinja2.*|Jinja2==2.8|g' ${OA_DIR}/global-requirement-pins.txt
  fi
  sed -i 's|^Jinja2.*|Jinja2==2.8|g' ${OA_DIR}/requirements.txt
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

  # Beginning with queens, the key must be 'aio_lxc'
  case ${RE_JOB_SCENARIO} in
    kilo|liberty|mitaka|newton|ocata|pike)
      key="aio"
      ;;
    *)
      key="aio_lxc"
      ;;
  esac

  echo "
  confd_overrides:
    $key:
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
  if [[ ! -z ${use_ovs+x} ]]; then
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
  if [[ ! -e /etc/openstack_deploy/user_resolvconf_fix.yml ]]; then
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

function update_kernel_extra {
    case ${RE_JOB_SCENARIO} in
      liberty)
        KERNEL_STRING="\"{% if hostvars[inventory_hostname]['ansible_kernel'] | version_compare('3.13.0-166', '>=') %}linux-modules-extra-{{ ansible_kernel }}{% else %}linux-image-extra-{{ ansible_kernel }}{% endif %}\""
        if [[ -n $(egrep -Rl linux-image-extra /opt/openstack-ansible/ 2> /dev/null) ]]; then
            sed -i "s/- linux-image-extra.*/- ${KERNEL_STRING}/g" $(egrep -Rl linux-image-extra /opt/openstack-ansible/ 2> /dev/null)
        fi
        ;;
      mitaka|newton)
        if [[ ${RE_JOB_IMAGE} == trusty ]]; then
            KERNEL_STRING="\\\\\"{% if hostvars[inventory_hostname]['ansible_kernel'] | version_compare('3.13.0-166', '>=') %}linux-modules-extra-{{ ansible_kernel }}{% else %}linux-image-extra-{{ ansible_kernel }}{% endif %}\\\\\""
            if [[ -n $(egrep -Rl linux-image-extra /etc/ansible/roles /opt/openstack-ansible 2> /dev/null) ]]; then
                SED_CMD="sed -i \"s/- linux-image-extra.*/- ${KERNEL_STRING}/g\" \$(egrep -Rl linux-image-extra /etc/ansible/roles /opt/openstack-ansible 2> /dev/null)"
                sed -i "/# Bootstrap an AIO/i ${SED_CMD}" ${OA_DIR}/scripts/gate-check-commit.sh
            fi
        elif [[ ${RE_JOB_IMAGE} == xenial ]]; then
            KERNEL_STRING="\\\\\"{% if hostvars[inventory_hostname]['ansible_kernel'] | version_compare('4.4.0-143', '>=') %}linux-modules-extra-{{ ansible_kernel }}{% else %}linux-image-extra-{{ ansible_kernel }}{% endif %}\\\\\""
            if [[ -n $(egrep -Rl linux-image-extra /etc/ansible/roles /opt/openstack-ansible 2> /dev/null) ]]; then
                SED_CMD="sed -i \"s/- linux-image-extra.*/- ${KERNEL_STRING}/g\" \$(egrep -Rl linux-image-extra /etc/ansible/roles /opt/openstack-ansible 2> /dev/null)"
                sed -i "/# Bootstrap an AIO/i ${SED_CMD}" ${OA_DIR}/scripts/gate-check-commit.sh
            fi
            if [[ -n $(egrep -Rl linux-modules-extra /opt/openstack-ansible/tests 2> /dev/null) ]]; then
                SED_CMD="sed -i \"s/- linux-modules-extra.*/- ${KERNEL_STRING}/g\" \$(egrep -Rl linux-modules-extra /opt/openstack-ansible/tests 2> /dev/null)"
                sed -i "/# Bootstrap an AIO/i ${SED_CMD}" ${OA_DIR}/scripts/gate-check-commit.sh
            fi
        fi
        ;;
      *)
        true
        ;;
    esac
}

function bootstrap_rpco {
  # Run these outside of deploy.sh and remove to prevent overriding changes
  sed -i 's/\(.\/scripts\/bootstrap-ansible.sh.*\)/#\1/' ${OA_DIR}/../scripts/deploy.sh
  sed -i 's/\(.\/scripts\/bootstrap-aio.sh.*\)/#\1/' ${OA_DIR}/../scripts/deploy.sh
  ./scripts/bootstrap-ansible.sh
  if [[ ${RE_JOB_SCENARIO} == "rpco-mitaka" ]]; then
    export BOOTSTRAP_OPTS=${BOOTSTRAP_OPTS:-"pip_get_pip_options='-c ${OA_DIR}/global-requirement-pins.txt'"}
    export UPPER_CONSTRAINTS_FILE="http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?id=$(awk '/requirements_git_install_branch:/ {print $2}' ${OA_DIR}/playbooks/defaults/repo_packages/openstack_services.yml) -U"
    sed -i "s@^#pip_install_upper_constraints.*@pip_install_upper_constraints: $UPPER_CONSTRAINTS_FILE@" /etc/ansible/roles/pip_install/defaults/main.yml
  fi
  ./scripts/bootstrap-aio.sh

  # Define rpco maas users
  cat > /etc/openstack_deploy/user_extras_secrets.yml << EOF
---
maas_rabbitmq_password:
maas_swift_accesscheck_password:
rpc_support_holland_password:
EOF

  if [[ ${RE_JOB_SCENARIO} == "rpco-liberty" ]]; then
    sed -i 's/\(apt-get -y.*\)/\1 --force-yes -o Dpkg::Options::="--force-confold"/' ${OA_DIR}/playbooks/roles/lxc_hosts/defaults/main.yml
    sed -i -e '/# configure the horizon extensions.*/,+2d' ${OA_DIR}/../scripts/deploy.sh
  elif [[ ${RE_JOB_SCENARIO} == "rpco-mitaka" ]]; then
    sed -i 's/\(apt-get -y.*\)/\1 --force-yes -o Dpkg::Options::="--force-confold"/' /etc/ansible/roles/lxc_hosts/vars/ubuntu-14.04.yml
  fi

  sed -i '/run_ansible maas-get.yml.*/,+d' ${OA_DIR}/../scripts/deploy-rpc-playbooks.sh
  sed -i 's/\(spicehtml5_git_repo\: \).*/\1https:\/\/gitlab.com\/spice\/spice-html5/' ${OA_DIR}/playbooks/defaults/repo_packages/openstack_other.yml
  sed -i -e '/ansible-galaxy install --role-file=\/opt\/rpc-openstack\/ansible-role-requirements.yml.*/,+1d' ${OA_DIR}/../scripts/deploy.sh
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

if [[ ! -d "/etc/openstack_deploy" ]]; then
  mkdir -p /etc/openstack_deploy
fi

if [[ ${RE_JOB_SCENARIO} == ceph ]]; then
  git clone https://github.com/rcbops/rpc-ceph.git /opt/rpc-ceph
  pushd /opt/rpc-ceph
    # Build rpc-ceph with the functional scenario, minus rpc-maas
    TEST_RPC_MAAS="False" RE_JOB_SCENARIO="functional" ./run_tests.sh
  popd

elif [[ ${RE_JOB_SCENARIO} == osp13 ]]; then
  git clone https://github.com/rcbops/osp-mnaio.git /opt/osp-mnaio
  pushd /opt/osp-mnaio
    export OSP_DEPLOY_VERSION=`echo ${RE_JOB_SCENARIO} | tr -d 'osp'`
    export OSP_JOB_ACTION=${RE_JOB_ACTION}
    export REDHAT_USERNAME=${RPC_OSP_REDHAT_USERNAME:-''}
    export REDHAT_PASSWORD=${RPC_OSP_REDHAT_PASSWORD:-''}
    export REDHAT_POOL_ID=${RPC_OSP_REDHAT_POOL_ID:-''}
    export REDHAT_ISO_URL=${RPC_OSP_REDHAT_ISO_URL:-''}
    export REDHAT_CONSUMER_NAME="osp-mnaio-PR-test"
    export REDHAT_OSP_VERSION=${OSP_DEPLOY_VERSION:-'13'}
    export REDHAT_OVERCLOUD_REGISTER="true"
    bash ./build.sh
  popd

else
    if [[ ${RE_JOB_SCENARIO#rpco-} == ${RE_JOB_SCENARIO} ]]; then
      export OA_DIR="/opt/openstack-ansible"

      if [[ ! -d "/opt/openstack-ansible" ]]; then
        git clone https://github.com/openstack/openstack-ansible /opt/openstack-ansible
      else
        pushd /opt/openstack-ansible
          git fetch --all
        popd
      fi
    else
      export OA_DIR="/opt/rpc-openstack/openstack-ansible"
      export DEPLOY_AIO=yes
      export DEPLOY_RPC=no
      export DEPLOY_OA=yes
      export DEPLOY_HAPROXY=yes
      export DEPLOY_ELK=no
      export DEPLOY_MAAS=no
      export DEPLOY_CEPH=no
      export DEPLOY_SWIFT=no
      export DEPLOY_CEILOMETER=no
      export DEPLOY_TEMPEST=no
      export DEPLOY_MAGNUM=no
      export DEPLOY_HARDENING=no
      export FORKS=15

      if [[ ! -d "/opt/rpc-openstack" ]]; then
        git clone --recursive -b ${RE_JOB_SCENARIO#rpco-} https://github.com/rcbops/rpc-openstack /opt/rpc-openstack
      else
        pushd /opt/rpc-openstack
          git fetch --all
        popd
      fi
    fi

    pushd ${OA_DIR}
      if [[ "${RE_JOB_SCENARIO}" == "kilo" ]]; then
        git checkout "97e3425871659881201106d3e7fd406dc5bd8ff3"  # Last commit of Kilo
        update_kernel_extra
        pin_jinja
        pin_galera "5.5"
        # NOTE(cloudnull): In kilo we had a broken version of the ssh plugin listed in the role
        #                  requirements file. This patch gets the role from master and puts
        #                  into place which satisfies the role requirement.
        mkdir -p /etc/ansible/roles

      elif [[ "${RE_JOB_SCENARIO}" == "rpco-liberty" ]]; then
        update_kernel_extra
        pin_jinja
        # NOTE(tonytan4ever): temporary workaround to get around sshd versioning issue
        sed -i -e 's/0.4.4/v0.4.4/g' ${OA_DIR}/ansible-role-requirements.yml
        # Change Affinity - only create 1 galera/rabbit/keystone/horizon and repo server for testing MaaS
        sed -i 's/\(_container\: \).*/\11/' ${OA_DIR}/etc/openstack_deploy/openstack_user_config.yml.aio

        bootstrap_rpco
        pin_galera "10.0"
        spice_repo_fix

      elif [[ "${RE_JOB_SCENARIO}" == "liberty" ]]; then
        git checkout "06d0fd344b5b06456a418745fe9937a3fbedf9b2"  # Last commit of Liberty
        update_kernel_extra
        pin_jinja
        pin_galera "10.0"
        # NOTE(tonytan4ever): temporary workaround to get around sshd versioning issue
        sed -i -e 's/0.4.4/v0.4.4/g' /opt/openstack-ansible/ansible-role-requirements.yml
        # Change Affinity - only create 1 galera/rabbit/keystone/horizon and repo server for testing MaaS
        sed -i 's/\(_container\: \).*/\11/' /opt/openstack-ansible/etc/openstack_deploy/openstack_user_config.yml.aio
        # NOTE(npawelek): Prevent config file modification prompts and default to existing
        sed -i '/DEBIAN_FRONTEND=noninteractive apt-get install iptables-persistent/ s/install/install -y --force-yes -o Dpkg::Options::="--force-confold"/' /opt/openstack-ansible/scripts/run-playbooks.sh
        spice_repo_fix

      elif [[ "${RE_JOB_SCENARIO}" == "rpco-mitaka" ]]; then
        update_kernel_extra
        pin_jinja
        # NOTE(tonytan4ever): temporary workaround to get around sshd versioning issue
        sed -i -e 's/0.4.4/v0.4.4/g' ${OA_DIR}/ansible-role-requirements.yml
        # Change Affinity - only create 1 galera/rabbit/keystone/horizon and repo server for testing MaaS
        sed -i 's/\(_container\: \).*/\11/' ${OA_DIR}/etc/openstack_deploy/openstack_user_config.yml.aio

        bootstrap_rpco
        pin_galera "10.0"
        spice_repo_fix

      elif [[ "${RE_JOB_SCENARIO}" == "mitaka" ]]; then
        git checkout "fbafe397808ef3ee3447fe8fefa6ac7e5c6ff144"  # Last commit of Mitaka
        update_kernel_extra
        pin_jinja
        pin_galera "10.0"
        export OA_DIR="/opt/openstack-ansible"
        export BOOTSTRAP_OPTS=${BOOTSTRAP_OPTS:-"pip_get_pip_options='-c ${OA_DIR}/global-requirement-pins.txt'"}
        export UPPER_CONSTRAINTS_FILE="http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?id=$(awk '/requirements_git_install_branch:/ {print $2}' playbooks/defaults/repo_packages/openstack_services.yml) -U"
        spice_repo_fix
        # NOTE(tonytan4ever): temporary workaround to get around sshd versioning issue
        sed -i -e 's/version: 0.4.4/version: v0.4.4/g' /opt/openstack-ansible/ansible-role-requirements.yml

      elif [[ "${RE_JOB_SCENARIO}" == "newton" ]]; then
        git remote add rcbops-fork https://github.com/rcbops/openstack-ansible.git
        git fetch --all
        git checkout -b newton-fix rcbops-fork/stable/newton
        update_kernel_extra
        # NOTE(tonytan4ever): newton needs this to get around gating:
        # https://rackspace.slack.com/archives/CAD5VFMHU/p1525445460000172
        add_lxc_overrides
        if [[ "${RE_JOB_IMAGE}" == "trusty" ]]; then
          export UPPER_CONSTRAINTS_FILE="http://git.openstack.org/cgit/openstack/requirements/plain/upper-constraints.txt?id=$(awk '/requirements_git_install_branch:/ {print $2}' playbooks/defaults/repo_packages/openstack_services.yml) -U"
        fi

      elif [[ "${RE_JOB_SCENARIO}" == "ocata" ]]; then
        git checkout "stable/ocata"  # Branch checkout of Ocata (Current Stable)

      elif [[ "${RE_JOB_SCENARIO}" == "pike" ]]; then
        git checkout "stable/pike"  # Branch checkout of Pike (Current Stable)
        # Pin flask so it stops breaking xenial and other versions
        echo "Flask==0.12.2" >> /opt/openstack-ansible/global-requirement-pins.txt

      elif [[ "${RE_JOB_SCENARIO}" == "queens" ]]; then
        git checkout "stable/queens"  # Branch checkout of Queens (Current Stable)
        export ANSIBLE_INVENTORY="/opt/openstack-ansible/inventory"

      elif [[ "${RE_JOB_SCENARIO}" == "rocky" ]]; then
        git checkout "stable/rocky"  # Branch checkout of Rocky (Current Stable)
        export ANSIBLE_INVENTORY="/opt/openstack-ansible/inventory"

      elif [[ "${RE_JOB_SCENARIO}" == "stein" ]]; then
        git checkout "stable/stein"  # Branch checkout of Stein (Current Stable)
        export ANSIBLE_INVENTORY="/opt/openstack-ansible/inventory"

      elif [[ "${RE_JOB_SCENARIO}" == "train" ]]; then
        git checkout "stable/train"  # Branch checkout of Train (Current Stable)
        export ANSIBLE_INVENTORY="/opt/openstack-ansible/inventory"
      fi

      # Install ovs agent if applicable
      install_ovs

      # Disable tempest on newer releases
      if [[ -f "tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2" ]]; then
        sed -i 's|^tempest_install.*|tempest_install: no|g' tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2
        sed -i 's|^tempest_run.*|tempest_run: no|g' tests/roles/bootstrap-host/templates/user_variables.aio.yml.j2
      fi

      # Disable tempest on older releases
      sed -i '/.*run-tempest.sh.*/d' scripts/gate-check-commit.sh  # Disable the tempest run

      # NOTE(npawelek): Rocky requires a different version to be set, all other
      # releases work with the existing pin
      case ${RE_JOB_SCENARIO} in
        rocky|stein|train)
          true
          ;;
        *)
          echo "python-ldap<3;python_version=='2.7'" >> ${OA_DIR}/global-requirement-pins.txt
          ;;
      esac

      # Disable the sec role
      disable_security_role

      # Setup an AIO
      if [[ ${RE_JOB_SCENARIO#rpco-} == ${RE_JOB_SCENARIO} ]]; then
        sudo -H --preserve-env ./scripts/gate-check-commit.sh
      else
        pushd /opt/rpc-openstack
        sudo -H --preserve-env ./scripts/deploy.sh
        popd
      fi

    popd
fi

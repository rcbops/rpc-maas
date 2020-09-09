#!/bin/bash

# set -x

# give some time for cloud-init to do its thing
sleep 40

source ~/openstackclient_venv/bin/activate

ACCESSIP=$(openstack --os-cloud phobos server show rpc-maas-${JOB_NAME}-${GITHUB_RUN_ID}-${GITHUB_RUN_NUMBER} | awk "/${NETWORK}/{print \$4}" | awk -F '=' '{print $2}')

# Clone the repo.
/usr/bin/ssh -i ~/.ssh/id_rsa  -o "PasswordAuthentication=no" -o "StrictHostKeyChecking=no" -o "UserKnownHostsFile=/dev/null" -l ${IMAGE_USER} $ACCESSIP "
export RE_JOB_SCENARIO=${RE_JOB_SCENARIO}
export RE_JOB_IMAGE=${RE_JOB_IMAGE}
export RE_JOB_ACTION=${RE_JOB_ACTION}
export RE_JOB_BRANCH=${RE_JOB_BRANCH}
export REPO_URL=${REPO_URL}
export PUBCLOUD_USERNAME=${PUBCLOUD_USERNAME}
export PUBCLOUD_API_KEY=${PUBCLOUD_API_KEY}
export PUBCLOUD_TENANT_ID=${PUBCLOUD_TENANT_ID}
git clone $REPO_URL
cd rpc-maas
git fetch -va
git checkout ${RE_JOB_BRANCH}
git branch

# Run the test
sudo --preserve-env ./gating/gate/run
"

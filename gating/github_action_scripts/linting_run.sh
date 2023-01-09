#!/bin/bash

set -x

SELFINSTALL_PIP=false

if [ $SELFINSTALL_PIP == true ]; then
  if which pip; then
      sudo apt-get -y remove python3-pip python-pip
  fi
  if which virtualenv; then
      sudo apt-get -y remove virtualenv
  fi

  # Set to path to make sure we can hit the new pip and virtualenv commands
  export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/home/runner/.local/bin:/home/runner/.local/sbin

  # Download and run the pip installer
  curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py
  python3 /tmp/get-pip.py 'setuptools==50.3.2' 'virtualenv==20.2.1'
fi

# Install some dependancies
pip install bindep tox

# Run the tox tests
tmp_tox_dir=$(mktemp -d)
tox -e $RE_JOB_SCENARIO --workdir $tmp_tox_dir


#!/bin/bash

set -x

# Remove pip and virtualenv from container so we
# can install our own.
if which pip; then
    sudo apt-get -y remove python-pip
fi
if which virtualenv; then
    sudo apt-get -y remove virtualenv
fi

# Set to path to make sure we can hit the new pip and virtualenv commands
export PATH=$PATH:/usr/local/bin:/usr/local/sbin:/home/runner/.local/bin:/home/runner/.local/sbin

# Download and run the pip installer
curl --silent --show-error --retry 5 https://bootstrap.pypa.io/get-pip.py > /tmp/get-pip.py
python2.7 /tmp/get-pip.py 'setuptools==39.0.1' 'virtualenv<20'

# Install some dependancies
pip install bindep tox

# Run the tox tests
tmp_tox_dir=$(mktemp -d)
tox -e $RE_JOB_SCENARIO --workdir $tmp_tox_dir


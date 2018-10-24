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

## Vars ----------------------------------------------------------------------
export TEST_DIR="$(readlink -f $(dirname ${0}))"

## Main ----------------------------------------------------------------------
bash -vc "${TEST_DIR}/env-prep.sh"

# Build AIO
bash -vc "${TEST_DIR}/aio-create.sh"

# Run functional rpc-maas deployment
bash -vc "${TEST_DIR}/test-ansible-functional.sh"

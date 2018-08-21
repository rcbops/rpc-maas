#!/usr/bin/env python
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


import os
import sys
import mock
import unittest

current_path = os.path.abspath(
    os.path.dirname(os.path.realpath(__file__))
)
inventory_path = os.path.join(current_path, '..')
sys.path.append(inventory_path)

import rpcr_dynamic_inventory


class TestRpcrDynamicInventory(unittest.TestCase):

    def setUp(self):
        temp_rpcr_static_inv = open("current_path")

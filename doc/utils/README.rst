maas_checks_util.py
===================

The ``maas_checks_util`` module includes a ``check_details`` generator
which yields check names and corresponding details about them. These
include the alarms within each check as well as the criteria that
MaaS evaluates in order to trigger an alarm status. It additionally
includes any variables that can be configured to change how a given
alarm operates. The current use for this module is within the
documentation so it can be fully automated, rather than hand generated.

Requirements
------------

This module requires at least Python 3.6.

See requirements.txt for version requirements of the module's
dependencies, including Ansible, PyYAML, and Jinja2.

Usage
-----

This module is used from within the rcbops/privatecloud-docs repo
from a Sphinx extension. That extension checks out this repo,
runs `pip install -r requirements.txt`, and then imports and uses
the ``check_details`` generator. In order to develop and use this
module locally while contributing to it, you'll need to create a
virtualenv and install those same requirements. ::

    python3.6 -m venv maas-util-env
    source maas-util-env/bin/activate
    pip install -r requirements.txt

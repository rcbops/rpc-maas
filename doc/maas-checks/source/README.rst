:orphan:

maas_checks_config.py
=====================

The ``maas_checks_config`` module includes a ``check_details`` generator
which yields check names and corresponding details about them,
as well as a ``categorized_check_details`` function which returns check names
and their corresponding details within a dictionary organized by check
category.

These include the alarms within each check as well as the criteria that
MaaS evaluates in order to trigger an alarm status. It additionally
includes any variables that can be configured to change how a given
alarm operates. The current use for this module is within the
documentation so it can be fully automated, rather than hand generated.

Requirements
------------

As the docs build itself requires Python 2.7, this module should
continue to use 2.7.

See requirements.txt for version requirements of the module's
dependencies, including Ansible, PyYAML, and Jinja2.

Usage
-----

This module is used from within the rcbops/privatecloud-docs repo
from a Sphinx extension. That extension checks out this repo,
runs `pip install -r requirements.txt`, and then imports and uses
the ``categorized_check_details`` function. In order to develop and use this
module locally while contributing to it, you'll need to create a
virtualenv and install those same requirements. ::

    virtualenv -p python2.7 maas-util-venv
    source maas-util-env/bin/activate
    pip install -r requirements.txt

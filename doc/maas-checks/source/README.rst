:orphan:

To build the docs, execute ``tox -e check-docs``.

maas_checks_plugin.py
=====================

The ``maas_checks_plugin`` module is a Sphinx extension that renders
reStructuredText pages out of rpc-maas check templates along with their
variables. It creates both a single-page view of all available checks
and their alarms, as well as a per-category breakdown of the checks
and alarms.

Descriptions for categories, checks, and alarms can be added by using the
appropriate files in the ``stubs`` directory, which is laid out as
``stubs/{category}/{check}/``. Each category and check directory should
include a ``title.rst`` which is the category or check wide description and
will appear directly beneath the respective title in the output document.
For specific alarms within a check, the check's directory should include
a file with the alarm's exact name and the ``.rst`` suffix.

If any of the stub files are not found, a warning will be raised by the
Sphinx build. If files are found but they are empty, an informational
message will be logged to the build output.

NOTE: Do not use =, -, or * as any potential section headers you create
inside any of the stub files. Those are already in use for the structure
of the rest of the document.

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

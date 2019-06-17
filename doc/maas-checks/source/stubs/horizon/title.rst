The categorization of Horizon monitoring is driven by plugin
`horizon_check.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/horizon_check.py>`_.
The plugin runs a synthetic check that logs into the Horizon dashboard
and confirms existence of a specific value. The plugin is run
contextually on the ``horizon`` inventory group.

.. note::

    Due to changes in the Apache virtual host configuration for Horizon
    in Mikata (v13) onward, the plugin was forced to utilize the VIP to
    validate the current dashboard status. As a result, we no longer
    verify each horizon backend and all duplicate checks are disabled
    except on the ``horizon[0]`` inventory node.

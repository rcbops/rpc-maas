The categorization of Ceph monitoring is driven by the plugin
`ceph_monitoring.py
<https://github.com/rcbops/rpc-maas/blob/master/playbooks/files/rax-maas/plugins/ceph_monitoring.py>`_,
which runs locally on all nodes in the cluster. At deployment time, the
playbooks generate a custom monitoring client keyring named
``ceph.client.raxmon.keyring``, which is used to provide access to the
Ceph cluster. There are four different primary functions this plugin is
utilized for: ``cluster_stats``, ``mon_stats``, ``osd_stats``, and
``rgw_stats``. Each of which is run in context of the specific nature of
the check. Check templates are deployed to each role-specific node in
the Ceph cluster provided by the defined inventory groups.

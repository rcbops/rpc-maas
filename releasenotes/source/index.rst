Release notes
=============

Bond detection
--------------

Bond detection now reads the host's interface facts once, avoiding repeated
``hostvars`` expansion on controllers with thousands of network interfaces.
All bonding interfaces remain eligible for monitoring, including names other
than ``bond0`` and ``bond1``. Explicit ``maas_bonding_interfaces`` overrides
continue to take precedence.

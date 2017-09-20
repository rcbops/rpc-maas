#!/bin/bash
if [ -d "/opt/rpc-ceph" ]; then
  rm -rf /opt/rpc-ceph
fi

git clone https://github.com/andymcc/rpc-ceph /opt/rpc-ceph

export RPC_MAAS_DIR="$(pwd)"
pushd /opt/rpc-ceph
  bash /opt/rpc-ceph/run_tests.sh
popd

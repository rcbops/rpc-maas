#!/usr/bin/env bash

pushd /opt
  wget -P /opt/ https://storage.googleapis.com/golang/go1.11.1.linux-amd64.tar.gz
  tar  -xzf /opt/go1.11.1.linux-amd64.tar.gz -C /opt/
popd

pushd /usr/local/bin
  find /opt/go/bin/ -type f -exec ln -sf {} \;
popd

if ! grep -qw 'GOROOT="/opt/go"' /etc/environment; then
  echo 'GOROOT="/opt/go"' | tee -a /etc/environment
fi

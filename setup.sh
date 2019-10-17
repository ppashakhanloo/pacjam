#!/bin/bash

# Dependencies
apt-get install -y debhelper
apt-get install -y bear

# Hooking into build system
sudo mv /usr/bin/make /usr/bin/make-orig
cp aux/make /usr/bin/
cp aux/buildflags.conf /etc/dpkg/

# Setup for lzload
LZLOAD_PATH=$HOME/var/lib/lzload

if [ ! -d $LZLOAD_PATH ]; then
  mkdir -p $LZLOAD_PATH/symbol-out
fi

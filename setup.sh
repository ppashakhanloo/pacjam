#!/bin/bash

# Dependencies
apt-get install -y debhelper
apt-get install -y bear

# Hooking into build system
if [ ! -f /usr/bin/make-orig ]; then
  sudo mv /usr/bin/make /usr/bin/make-orig
  cp aux/make /usr/bin/
fi

if [ ! -f /usr/bin/gcc-orig ]; then
  sudo mv /usr/bin/gcc /usr/bin/gcc-orig
  cp aux/gcc /usr/bin/
fi

if [ ! -f /usr/bin/g++-orig ]; then
  sudo mv /usr/bin/g++ /usr/bin/g++-orig
  cp aux/g++ /usr/bin/
fi 

cp aux/buildflags.conf /etc/dpkg/

# Setup for lzload
LZLOAD_PATH=$HOME/var/lib/lzload

if [ ! -d $LZLOAD_PATH ]; then
  mkdir -p $LZLOAD_PATH/symbol-out
fi

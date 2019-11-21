#!/bin/bash

# Dependencies
sudo apt-get install -y debhelper
sudo apt-get install -y bear

# Hooking into build system
if [ ! -f /usr/bin/make-orig ]; then
  sudo mv /usr/bin/make /usr/bin/make-orig
fi
sudo cp aux/make /usr/bin/

if [ ! -f /usr/bin/gcc-orig ]; then
  sudo mv /usr/bin/gcc /usr/bin/gcc-orig
fi
sudo cp aux/gcc /usr/bin/

if [ ! -f /usr/bin/g++-orig ]; then
  sudo mv /usr/bin/g++ /usr/bin/g++-orig
fi 
sudo cp aux/g++ /usr/bin/

if [ ! -f /usr/bin/ld-orig ]; then
  sudo mv /usr/bin/ld /usr/bin/ld-orig
fi 
sudo cp aux/ld /usr/bin/

# Setup for lzload
LZLOAD_PATH=$HOME/var/lib/lzload

if [ ! -d $LZLOAD_PATH ]; then
  mkdir -p $LZLOAD_PATH/symbol-out
fi

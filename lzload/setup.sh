#!/bin/bash

# script assumes dep-symbol is on the path

LZLOAD_PATH=$HOME/var/lib/lzload

if [ ! -d $LZLOAD_PATH ]; then
  mkdir -p $LZLOAD_PATH/symbol-out
fi

# For tests
sudo apt-get install libpsl-dev

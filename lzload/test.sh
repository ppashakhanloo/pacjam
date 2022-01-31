#!/bin/bash

export LZLOAD_LIB="libpsl.so.5:libm.so.6"

export LZ_LIBRARY_PATH="/lib/x86_64-linux-gnu/:/usr/lib/x86_64-linux-gnu/" 
export LD_PRELOAD=/usr/local/lib/liblzload.so

build/loading-test

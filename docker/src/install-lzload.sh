#!/bin/bash

git clone https://github.com/petablox/lzload.git

cd lzload
export LANG=C

mkdir build && \ 
cd build && \
CC=clang cmake .. && \
make && \
sudo make install


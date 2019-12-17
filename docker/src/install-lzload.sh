#!/bin/bash

git clone https://github.com/petablox/lzload.git

cd lzload
export LANG=C

mkdir build && \ 
cd build && \
cmake .. && \
make && \
sudo make install


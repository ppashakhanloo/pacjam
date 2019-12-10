#!/bin/bash

git clone https://github.com/petablox/llvm.git

cd llvm && \
mkdir build && \
cd build && \
CC=clang CXX=clang++ \
	cmake -DCMAKE_BUILD_TYPE=Release \
	-DCMAKE_EXE_LINKER_FLAGS="-static-libstdc++" \
	-DLLVM_ENABLE_PROJECTS="clang;lld" \
	-G "Unix Makefiles" ../llvm && \
make


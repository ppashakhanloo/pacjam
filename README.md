# Overview

Repository is a suite of tools for manipulating debian packages. At a high level, dep-find generates a dependency list for use with dep-symbol and dep-src. I have also created a script, dep-all.sh, that chains the use of all three scripts together.

# dep-find

This tool builds a dependency graph of the debian packages cached by apt. I have incluced the files ``direct.txt`` and ``transitive.txt`` which show the direct and transitive dependencies for debian packages respectively. 

You can grab a dependency list for a package with:
```
./dep-find.py -p PACKAGE
```

which will create a file ``PACKAGE.dep`` in the current working directory. This can then be feed into ``dep-symbols``. For example, ``./dep-find.py -p wget`` will get the dependencies for ``wget`` and create ``wget.dep``.

You might also find it useful to search for dependecies and packages with ``apt``: ``apt-cache depends PACKAGE`` and ``apt-cache search PACKAGE``.  

# dep-symbol

Tool uses a dependency list for a package (built from dep-find.py) to download all dependencies and build a small repository of those dependency that contain symbol information.

## Install

All that is required for ``dep-symbol`` itself is a working python installation. Once you've pulled the repository, you can kickoff the ``test.sh`` script to make sure ``dep-symbol`` works. I've done my work on fir02, and have hardcoded the test script to use a copy of ``jq`` in my local installation directory (``/home/acanino/local``). If you do not run on fir02, you'll have to setup ``jq`` yourself and modify the test script. 

## Usage

### 1. Generate symbol repository for dependency list

```
mkdir symbol-out
./dep-symbol.py -d symbol-out wget.dep
```

# lzload

lzload is a C library that does the actual shim / dummy library loading at runtime. Build and install with cmake:

```
cd lzload
mkdir build && cd build
cmake .. -DCMAKE_C_COMPILER=/path/to/clang 
make
sudo make install
```

# dep-src

## Install

Run setup.sh to install dependencies and place the necessary make/dpkg-buildflags files on the system (this will require root). This will also setup a local symbol repository for lzload to use at runtime at $HOME/var/symbol-out.

## Usage

### 1. Building a dependency list

dep-src downloads and builds debian source packages from a dependency list. 

```
./dep-find.py -p wget
mkdir src-out
./dep-src.py -d src-out wget.dep
```

### 2. Generating symbol database

Generate a symbol repository for lzload to use to help find the correct symbol / library mapping at runtime. 

```
./dep-symbol.py -d $HOME/var/symbol-out wget.dep
```

### 3. Build dummy libraries

Generate dummy libraries for use with lzload. The following will attempt to build the dummy libraries and then store them in src-out/lib

```
mkdir src-out
./dep-src.py -d src-out wget.dep
```

### 4. Running with the dummy libraries.

There is a script at the top level, wget.sh, that demonstrates what environmnet variables need to be set to hook into the dummy libs. We need to set three environment variables: ``LZLOAD_LIB``, ``LZ_LIBRARY_PATH``, and ``LD_LIBRARY_PATH``.

``LZLOAD_LIB`` contains a colon seperate list of libraries that lzload should intercept. ``LZ_LIBRARY_PATH`` points to the actual path of the real libraries that lzload should load on a fault. ``LD_LIBRARY_PATH`` must point to the dummy libraries and liblzload.so. 
~

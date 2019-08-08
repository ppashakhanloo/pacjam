# dep-symbol

Tool uses a dependency list for a package (built from Kihongs scripts) to download all dependencies and build a small repository of those dependency that contain symbol information. We then build the package we are tracing with a modified LLVM that instruments code to dump LLVM IR call instructions invoked at runtime, generating a trace. The tool then uses the trace and symbol repository to see if any invoked functions match up with the dependencies. Crude, but it does work for some cases.

Please see the [google doc](https://docs.google.com/document/d/1DJzJAaDPN94_ZdD39uNFcFySFgTIDlI41zmcGUhyxKs/edit) for some notes about the tool.

## Build

All that is required for ``dep-symbol`` itself is a working python installation. Once you've pulled the repository, you can kickoff the ``test.sh`` script to make sure ``dep-symbol`` works. I've done my work on fir02, and have hardcoded the test script to use a copy of ``jq`` in my local installation directory (``/home/acanino/local``). If you do not run on fir02, you'll have to setup ``jq`` yourself and modify the test script. 

## Usage

### 1. Building target dependency with modified compiler

First, select a package or linux utility to gather dependency information for and grab the raw source. We will have to compile the target utility with the modified LLVM compiler. On fir02, the path for this compiler is ``/home/acanino/Projects/package-manager-debloat/llvm-kihong/build``. It's simplest to use my copy directly for the time being. For the remainder of the doc, I'll assume KLLVM is set to this path. 

As long as the source can be built with the modified compiler, it should be able to be run and generate a compatible trace. The actual command to compile some source would be:
```
${KLLVM}/bin/clang -trace-extract -L${KLLVM}/lib -lTracePrint hello.c -o a.out
```

For the standard linux autotools build system, you can set the following environment variables before kicking off ``configure``:
```
export CC=${KLLVM}/bin/clang
export CFLAGS="-trace-extract -g"
export LDFLAGS=-L${KLLVM}/lib
export LIBS=-lTracePrint
```

Once you successfully build a target dependency with the modified compiler, running the built program will generate a trace file in the current working directory called ``analysis-out/trace.txt``.

### 2. Checking for runtime dependency use

Once you have a trace for a target dependency, you can feed it into the ``dep-symbol.py`` tool along with a dependency list [generated from dep-find.py](#dep-find) to get some information on runtime dependency usage:

```
./dep-symbol.py -t path/to/trace.txt path/to/trace.dep
```

``dep-symbol`` will build a repository of symbol information (defaulting to ``./symbol-out``) by downloading the debian packages from the supplied dependency list. If there is no symbol information for a debian package, ``dep-symbol`` will attempt to generate a ``symbols`` file. 

``dep-symbol`` can generate JSON about runtime dependency information for post-processing by supplying ``-o out.json``.


# dep-find

This tool (written by Kihong) builds a dependency graph of the debian packages cached by apt. I have incluced the files ``direct.txt`` and ``transitive.txt`` which show the direct and transitive dependencies for debian packages respectively. 

For the time being, you can grab a dependency list for a package with:

```
./dep-find.py -p PACKAGE
```

which will create a file ``PACKAGE.dep`` in the current working directory. This can then be feed into ``dep-symbols``. For example, ``./dep-find.py -p wget`` will get the dependencies for ``wget`` and create ``wget.dep``.

You might also find it useful to search for dependecies and packages with ``apt``: ``apt-cache depends PACKAGE`` and ``apt-cache search PACKAGE``.



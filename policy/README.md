# Statistical installation policy

## [fetch.py](policy/fetch.py)
This script downloads all popcond data (from the beginning to Oct. 4 2019) of packages in [deps.json](deps.json).
To save network traffic, all the data are already sotred in [popcon-data](popcon-data).
By default, this script skips downloading data of package X if `popcon-data/X.json` exists or
X is in [blacklist.json](popcon-data). The black list contains a set of packages whose popcon data does not exist.

Later, the script should be updated to continuously collect new data.

## [statistics.py](policy/statistics.py)
This script generates statistics for each package `X` and stores the data in `popcon-data/X.daily.json`.
For each date, it computes a binary value whether a package is used in that day. The statistical data files
are not stored in the git repository since the process is fast enough.

## [bnet-generator.py](policy/bnet-generator.py)
This script generates the Bayesian network for package dependency graph of a given package
(provided as a commandline argument).
The Bayesian network is described as a factor graph.
The format is described [here](https://staff.fnwi.uva.nl/j.m.mooij/libDAI/doc/fileformats.html).

We use the [LibDai](https://staff.fnwi.uva.nl/j.m.mooij/libDAI) inference solver, which is a part of
Nichome.
```
git clone --recurse-submodules https://github.com/nichrome-project/nichrome.git
cd nichrome/main
ant
pushd libsrc
cp libdai/Makefile.LINUX libdai/Makefile.conf
make -j
```

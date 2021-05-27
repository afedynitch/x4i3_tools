# x4i3_tools - Support tools for x4i3 (The EXFOR Interface [for Python 3])

The [`x4i3`](https://github.com/afedynitch/x4i3) project requires a preprocessed version of the EXFOR database that is usually distributed by the [International Atomic Energy Agency (IAEA)](https://www-nds.iaea.org/nrdc/) (probably via mail and FTP or CD-ROM). The last version of a zip-file that I obtained from somewhere was from 2016-04-01, which is attach as a binary file to this release.

The contained files are a fork of the original project `x4i` developed by David A. Brown (LLNL, Livermore CA, 94550).

Since the main objective of this *support tools* is to keep `x4i3` alive and working, not all of its parts have been debugged and ported. These tools shall be considered as work in progress and there is no guarantee for stability and correctness. The no warranty/liability blurb is located in the [license](LICENCE).

Completely untouched are the utilities related to the graph networks applications possible with x4i. Given the amount of code in [graph_tools](graph_tools), it does likely something mysterious and interesting. But their purpose is quite opaque to me and any help to get them going is greatly appreciated.

## Notable updates

This version of the tools supports the later database zip files `X4-20XX-XX-XX.zip` that contain three-digit named sub-folders with `*.x4` files directly. Major performance improvement through multi-threading and transaction based fill of the mysql database.

## Installation

Since this stuff is geeky, there is no PyPi package or similar provided. Download the project through git clone.

## Usage

The main tool is `setup_exfor_db.py`. Run

    python setup_exfor_db.py --help

to get an idea of the purpose. A typical use case is the conversion of an EXFOR master zip-file into the tables and index files required to run `x4i3` through

    python setup_exfor_db.py --X4-master <name_of_the_zipped_EXFOR_master>

It will create a directory named after the EXFOR master file, the sqlite tables and several pickled files. The content of this directory is distributed as tar.gz with `x4i3`. The latest update makes this process fast if you have multiple threads. By default 75% of threads are used or provided via `-ncpu` argument.

## Documentation

No documentation!

(Maybe there is something in the original x4i documentation but outdated since this code doesn't mess with the files of the x4i3 package anymore.)

## Contributions

..are welcome. There are two folders `requires_work` and `graph_tools`. They seem to do fancy stuff with the database but not clear what.

## Authors

*David A. Brown (LLNL)* (`x4i`)

*Anatoli Fedynitch* (`x4i3_tools`)

## Copyright and license

Code released under GNU General Public License (GPLv2) [(see LICENSE)](LICENSE.txt).

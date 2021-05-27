# Modifications to this file have this license
# Copyright (c) 2020, Anatoli Fedynitch <afedynitch@gmail.com>

# This file is part of the fork (x4i3) of the EXFOR Interface (x4i)

# Please read the LICENCE.txt included in this distribution including "Our [LLNL's]
# Notice and the GNU General Public License", which applies also to this fork.

# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License (as published by the
# Free Software Foundation) version 2, dated June 1991.

# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# terms and conditions of the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

# Copyright (c) 2011, Lawrence Livermore National Security, LLC. Produced at
# the Lawrence Livermore National Laboratory. Written by David A. Brown
# <brown170@llnl.gov>.
#
# LLNL-CODE-484151 All rights reserved.
#
# This file is part of EXFOR Interface (x4i)
#
# Please also read the LICENSE.txt file included in this distribution, under
# "Our Notice and GNU General Public License".
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License (as published by the
# Free Software Foundation) version 2, dated June 1991.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the IMPLIED WARRANTY OF
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# terms and conditions of the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import argparse
import pickle
import os

import x4i3tools


def report_errors(outFile):
    import csv

    if x4i3tools.verbose:
        print('Error file name:', x4i3tools.currentErrorFileName)
    f = pickle.load(open(x4i3tools.currentErrorFileName, mode='rb'))

    sortedErrors = {}
    for i in f:
        t = type(f[i][0])
        if not t in sortedErrors:
            sortedErrors[t] = []
        sortedErrors[t].append(i)

    # Full report to a csv file
    if x4i3tools.verbose:
        print('Writing report to:', outFile)
    fullReport = csv.writer(open(outFile, mode='wb'))
    fullReport.writerow(["Error", "Number Occurances", "Entry", "Full Message"])
    for i in sortedErrors:
        for j in range(len(sortedErrors[i])):
            example = f[sortedErrors[i][j]][1]
            entry = sortedErrors[i][j].replace('.x4', '')
            if j == 0:
                row = [repr(i), str(len(sortedErrors[i])), entry, example]
            else:
                row = [" ", " ", entry, example]
            fullReport.writerow(row)


def view_errors():
    f = pickle.load(open(x4i3tools.currentErrorFileName, mode='rb'))

    sortedErrors = {}
    for i in f:
        t = type(f[i][0])
        if not t in sortedErrors:
            sortedErrors[t] = []
        sortedErrors[t].append(i)

    # Quick Report to stdout:
    print("Error".rjust(55), " ", "Num.", " ", "Example".ljust(74), " ", "Entry")
    for i in sortedErrors:
        for j in range(len(sortedErrors[i])):
            example = f[sortedErrors[i][j]][1]
            if len(example) > 70:
                example = example[0:70] + '...'
            example = example.ljust(74)
            entry = sortedErrors[i][j].replace('.x4', '')
            if j == 0:
                print(repr(i).rjust(55), " ", str(
                    len(sortedErrors[i])).ljust(4), " ", example, " ", entry)
            else:
                print(55 * " ", " ", 4 * " ", " ", example, " ", entry)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Manage the installation & update of x4i's internal copy of the EXFOR database.")
    parser.add_argument(
        "-v",
        action="store_true",
        dest='verbose',
        help="Enable verbose output")
    parser.add_argument(
        "-f",
        action="store_true",
        dest='force',
        help="Force overwriting working directories")
    parser.add_argument(
        "-ncpu",
        type=int,
        default=-1,
        dest='ncpu',
        help="Set number of threads in multiprocessing. Default is number of threads.")

    # ------- Control over update actions -------
    parser.add_argument(
        "--just-build-index",
        action="store_true",
        default=False,
        help="Just (re)builds the sqlite database indexing the EXFOR data in the project. The EXFOR data must be already unpacked.")
    parser.add_argument(
        "--just-unpack",
        action="store_true",
        default=False,
        help="Just unpack the EXFOR data, then stop. Do not (re)build the sqlite database index.")

    # ------- View/save logs -------
    parser.add_argument(
        "--view-errors",
        action="store_true",
        default=False,
        help="View all errors encountered while building the database index.")
    parser.add_argument(
        '--error-log',
        metavar="CSVFILE",
        type=str,
        default=None,
        help="Write all the errors encountered when generating the index of the EXFOR files to this file.  This is a csv formatted file suitable for viewing in MS Excel.")
    # parser.add_argument('--coupled-log', metavar="CSVFILE", type=str, default=None,
    # help="Write all the coupled data encountered when generating the index
    # of the EXFOR files to this file.  This is a csv formatted file suitable
    # for viewing in MS Excel.")

    parser.add_argument("--exfor-master", metavar='ZIPFILE', type=str, default=None,
                        help="""Install the (hopefully) IAEA generated EXFOR Master File [a zipfile] into the project,
            unpack the zipfile, then build the index.
            The file is available here:  http://www-nds.iaea.org/exfor-master/backup/?C=M;O=D""")

    parser.add_argument("--X4-master", metavar='ZIPFILE', type=str, default=None,
                        help="""Install the IAEA generated X4 Master File [a zipfile] into the project, unpack the zipfile, then build the index. This is the newer X4-xxx format files, rather than the original EXFOR-20xx-...zip files.
            The file is available here:  http://www-nds.iaea.org/exfor-master/backup/?C=M;O=D""")

    # ------- Update the EXFOR dicts. -------
    parser.add_argument("--dict", type=str, default=None,
                        help='Reinstall the EXFOR dictionaries using the contents from this IAEA EXFOR dictionary Transaction file.')
    parser.add_argument("--doi", type=str, default=None,
                        help='Reinstall the EXFOR doi <-> entry mapping using the contents from this IAEA EXFOR dictionary text file.')

    args = parser.parse_args()

    # Set verbosity level
    x4i3tools.verbose = args.verbose

    # Set force flag
    x4i3tools.force = args.force
    # Number of cores
    x4i3tools.nthreads = args.ncpu if args.ncpu > 0 else x4i3tools.nthreads

    assert args.exfor_master is not None or args.X4_master is not None, 'Chose either EXFOR or X4 format'

    if args.exfor_master is not None:
        from x4i3tools.fileops import unpackEXFORMaster as unpack_func
        x4_db_fname = args.exfor_master
        dbdir = 'db'
    else:
        from x4i3tools.fileops import unpackX4Master as unpack_func
        x4_db_fname = args.X4_master
        dbdir = 'X4all'

    # Set paths for all operations
    current_path = x4i3tools.set_current_dir(x4_db_fname, create=False)
    x4i3tools.currentDBPath = os.path.join(current_path, dbdir)

    if not (args.just_build_index or args.doi or args.error_log or args.view_errors):
        unpack_func(x4_db_fname)

    if not (args.just_unpack or args.doi or args.error_log or args.view_errors):
        from x4i3tools.index_generators import buildMainIndex, insertDOIIndex

        buildMainIndex()
        insertDOIIndex()

    if args.doi:
        from x4i3tools.index_generators import insertDOIIndex
        insertDOIIndex()

    if args.view_errors:
        view_errors()

    if args.error_log:
        report_errors(current_path + '.csv')

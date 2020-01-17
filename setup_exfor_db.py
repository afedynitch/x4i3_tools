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

from __future__ import print_function
from x4i3 import (
    indexFileName, errorFileName,
    coupledFileName, reactionCountFileName, monitoredFileName,
    dbPath
)
import sys
import os
import argparse
import collections

try:
    import cPickle as pickle
except BaseException:
    import pickle

# sys.path.append('d:/OneDrive/devel/git/x4i3')


buggyEntries = {}
coupledReactionEntries = {}
monitoredReactionEntries = {}
reactionCount = {}


def recreate_dir(path, force):
    import shutil
    if os.path.exists(path) and not force:
        raise IOError('Directory', path,
                      'already present use -f (force) flag to overwrite.')
    elif os.path.exists(path) and force:
        shutil.rmtree(path)
        os.makedirs(path)
    else:
        os.makedirs(path)


def set_current_dir(new_path):
    global currentIndexFileName, currentErrorFileName
    global currentCoupledFileName, currentMonitoredFileName
    global currentReactionCountFileName, currentDBPath

    print("set_current_dir(): New files will be stored in", new_path)
    currentIndexFileName = os.path.join(new_path, indexFileName)
    currentErrorFileName = os.path.join(new_path, errorFileName)
    currentCoupledFileName = os.path.join(new_path, coupledFileName)
    currentMonitoredFileName = os.path.join(new_path, monitoredFileName)
    currentReactionCountFileName = os.path.join(new_path, reactionCountFileName)
    currentDBPath = os.path.join(new_path, dbPath)


def unpackEXFORMaster(newZipFile, verbose, force):
    '''Unpack an EXFOR master file'''
    import shutil
    import glob
    import zipfile
    import x4i3.exfor_utilities

    # # Create target directory
    unpackedDir = os.path.splitext(os.path.relpath(newZipFile))[0]
    recreate_dir(unpackedDir, force)

    new_base_dir = os.path.join('x4i3_' + unpackedDir)
    recreate_dir(new_base_dir, force)
    set_current_dir(new_base_dir)

    if verbose:
        print("Unpacking master file: ", newZipFile)
    with zipfile.ZipFile(newZipFile, 'r') as zip_ref:
        zip_ref.extractall(unpackedDir)

    nfiles_written = 0
    # repackage the file
    backupFile = glob.glob(os.sep.join([unpackedDir, '*.bck']))[0]
    theLines = open(backupFile, mode='rb').readlines()
    for entry in x4i3.exfor_utilities.chunkifyX4Request(theLines):
        for line in entry:
            if 'ENTRY' in line:
                entryNum = line[17:22]
                break
        newX4Path = os.sep.join([currentDBPath, entryNum[0:3]])
        if not os.path.exists(newX4Path):
            os.makedirs(newX4Path)
        newX4File = entryNum + '.x4'
        open(newX4Path + os.sep + newX4File, mode='wb').writelines(''.join(entry))
        nfiles_written += 1

    print('In total', nfiles_written, 'have been extracted.')

    # cleanup
    shutil.rmtree(unpackedDir)


def buildMainIndex(verbose, force, stopOnException=False):
    '''
    This function build up the index of the database.

    The database is assumed to be in the ``x4i/data/db`` directory (set by the
    ``dbPath`` global variable).  The directory is arranged as follows ::

        db/001/00011.x4
               00012.x4
               ...
           002/00021.x4
               ...
          ...

    You can probable guess the columns in our sqlite3 database since we use this
    index to support the follow searches ::

        AUTHOR:
            author = None

        REACTION:
            reaction = None
            target = None
            projectile = None
            quantity = None
            product = None
            MF = None
            MT = None
            C = None
            S = None
            I = None

        SUBENT = None

        ENTRY = None

    '''
    import sqlite3
    import pprint
    import glob
    from x4i3 import exfor_exceptions
    import pyparsing

    def remove_if_force(file_name):
        if os.path.exists(file_name) and force:
            os.remove(file_name)
        elif os.path.exists(file_name):
            raise IOError('Can not overwrite file', file_name,
                          'Consider using -f (force) flag.')
    # clean up previous runs
    remove_if_force(currentIndexFileName)
    remove_if_force(currentErrorFileName)
    remove_if_force(currentCoupledFileName)
    remove_if_force(currentReactionCountFileName)
    remove_if_force(currentMonitoredFileName)

    # set up database & create the table
    connection = sqlite3.connect(currentIndexFileName)
    cursor = connection.cursor()
    cursor.execute('''create table if not exists theworks (entry text, subent text, pointer text, author text, reaction text, projectile text, target text, quantity text, rxncombo bool, monitored bool)''')

    # build up the table
    try:
        if verbose:
            print(os.sep.join([currentDBPath, '*', '*.x4']))
        for f in glob.glob(os.sep.join([currentDBPath, '*', '*.x4'])):

            if False:  # Then we are debugging
                skipme = True
               # "12763.20363.22188.22782.41434.41541.A0026.A0206.A0208.A0222.A0227.A0291.A0425.A0462
               # #.A0578.A0648.A0650.A0727.A0882.A0926.C0082.C0256.C0299.C0346.C1248.C1654.D0046.
               # D6011.D6043.D6170.E1306.E1792.E2324.E2371.G0016.G4035.M0763.M0806",
               # '20363.22188.22782.41434.41541'

                for myENTRYForTesting in '11125.30230'.split('.'):
                    if myENTRYForTesting in f:
                        skipme = False
                if skipme:
                    continue

            if verbose:
                print('    ', f)
            if stopOnException:
                processEntry(
                    f,
                    cursor,
                    coupledReactionEntries,
                    monitoredReactionEntries,
                    reactionCount,
                    verbose=verbose)
            else:
                try:
                    processEntry(
                        f,
                        cursor,
                        coupledReactionEntries,
                        monitoredReactionEntries,
                        reactionCount,
                        verbose=verbose)
                except (
                        exfor_exceptions.IsomerMathParsingError,
                        exfor_exceptions.ReferenceParsingError,
                        exfor_exceptions.ParticleParsingError,
                        exfor_exceptions.AuthorParsingError,
                        exfor_exceptions.InstituteParsingError,
                        exfor_exceptions.ReactionParsingError,
                        exfor_exceptions.BrokenNumberError) as err:
                    buggyEntries[f] = (err, str(err))
                    continue
                except (Exception, pyparsing.ParseException) as err:
                    buggyEntries[f] = (err, str(err))
                    continue
    except KeyboardInterrupt:
        pass
    except Exception as err:
        print("Encountered error:", repr(err), str(err))
        print("Saving work")

    # log all the errors
    if verbose:
        print('\nNumber of Buggy Entries:', len(buggyEntries))
    if verbose:
        print('\nBuggy entries:')
    if verbose:
        pprint.pprint(buggyEntries)
    pickle.dump(buggyEntries, open(currentErrorFileName, mode='wb'))

    # log all the coupled data sets
    if verbose:
        print('\nNumber of entries with coupled data sets:', len(coupledReactionEntries))
    if verbose:
        print(
            '\nNumber of entries with reaction monitors sets:',
            len(monitoredReactionEntries))
    if verbose:
        print('\nNumber of distinct reactions:', len(reactionCount))
    pickle.dump(coupledReactionEntries, open(currentCoupledFileName, mode='wb'))
    pickle.dump(monitoredReactionEntries, open(currentMonitoredFileName, mode='wb'))
    pickle.dump(reactionCount, open(currentReactionCountFileName, mode='wb'))

    # commit & close connection to database
    connection.commit()
    cursor.close()


def insertDOIIndex(verbose, force, doiFileName='x4doi.txt'):
    '''
    Adds the DOI cross reference table to the main index.
    The IAEA should probably tightly associated this data with
    the EXFOR data, but for some reason it is not.
    '''
    import sqlite3
    try:
        print('Inserting DOI info from', doiFileName, 'in', currentIndexFileName)
    except NameError as err:
        print('Current files not defined', err)
        exit()
    if not os.path.exists(doiFileName):
        raise IOError('DOi file not found')
    # set up database & create the table
    connection = sqlite3.connect(currentIndexFileName)
    cursor = connection.cursor()
    cursor.execute('''drop table if exists doiXref''')
    cursor.execute(
        '''create table doiXref (entry text, nsr text, doi text, reference text )''')

    for line in open(doiFileName).readlines():
        entry = line[32:46].strip().replace('$ENTRY=', '')
        nsr = line[46:61].strip().replace('$NSR=', '')
        doi = line[61:].strip().replace('$DOI=', '')
        reference = line[0:32].strip().replace('$REF=', '')
        cursor.execute("insert into doiXref values(?,?,?,?)",
                       (entry, nsr, doi, reference))

    # commit & close connection to database
    connection.commit()
    cursor.close()


def getQuantity(quantList):
    '''
    Most quantities are the 1st ones in the quantity list
    ... but there are a lot of important exceptions ...
    ... 'POT' is the exceptions to the exceptions ...
    '''
    for q in ['AA', 'AKE/DA', 'AKE', 'AMP', 'AP',
              'AP/DA', 'COR', 'COR/DE', 'CRL', 'DA/RAT', 'DA',
              'DA/DE', 'DA/DP', 'DA/CRL', 'DA/DA', 'DA/DA/DE',
              'DA/DE', 'DA/KE', 'DA/TMP', 'DE', 'FM/DA', 'FY',
              'FY/DE', 'FY/RAT', 'FY/SUM', 'FY/CRL', 'INT',
              'INT/DA', 'ISP', 'KE', 'KE/CRL', 'MCO', 'MLT',
              'NU', 'NU/DE', 'POL', 'POL/DA/DE', 'POL/DA',
              'POL/DA/DA/DE', 'RI', 'SPC', 'SPC/DMT/DR',
              'SPC/DPT/DR', 'SPC/DR', 'PY', 'SIG', 'SIG/RAT',
              'SIG/SUM', 'TTY', 'TTY/DA/DE', 'TTY/DA', 'WID',
              'WID/RED', 'WID/STR', 'ZP']:
        if q in quantList:
            return q
    if 'POT' in quantList:
        return 'POT'
    return quantList[0]


SimpleReaction = collections.namedtuple(
    "SimpleReaction", "proj targ prod rtext quant simpleRxn")


def getSimpleReaction(complicatedReaction):
    proj = repr(complicatedReaction.proj)
    targ = '-'.join(repr(complicatedReaction.targ).split('-')[1:])
    prod = '+'.join(map(repr, complicatedReaction.products)).replace("'", "")
    resid = repr(complicatedReaction.residual)
    rtext = (proj + "," + prod).upper()
    quant = getQuantity(complicatedReaction.quantity)
    if '-M' in resid:
        simpleRxn = (targ + '(' + rtext + ')' + resid, quant)
    else:
        simpleRxn = (targ + '(' + rtext + ')', quant)
    return SimpleReaction(proj, targ, prod, rtext, quant, simpleRxn)


def processEntry(entryFileName, cursor=None, coupledReactionEntries={},
                 monitoredReactionEntries={}, reactionCount={}, verbose=False):
    '''
    Computes the rows for a single entry and puts it in the database
    '''
    from x4i3 import exfor_entry, exfor_reactions
    if verbose:
        print('        ', entryFileName.split(os.sep)[-1], end=' ')
    e = exfor_entry.x4EntryFactory(entryFileName.split(os.sep)[-1].split('.')[0])
    doc_bib = e[1]['BIB']
    try:
        m = e.meta().legend()
        print(str(e.accnum) + ':', m)
    except Exception as err:
        m = None
        print()
    auth = []  # author field
    inst = []  # institute field
    if 'AUTHOR' in doc_bib:
        auth = doc_bib['AUTHOR'].author_family_names
    if 'INSTITUTE' in doc_bib:
        inst = doc_bib['INSTITUTE']
    if verbose:
        print('        ', "Num. authors:", len(auth))
        print('        ', "Num. institutes:", len(inst))
        print()

    for snum in e.sortedKeys()[1:]:
        rxnf = {}  # reaction field
        monf = None  # monitor field
        if 'BIB' in e[snum]:
            bib = e[snum]['BIB']
            if 'REACTION' in bib:
                rxnf = bib['REACTION']
            if 'MONITOR' in bib:
                monf = bib['MONITOR']
        if auth == [] and 'AUTHOR' in doc_bib:
            auth = doc_bib['AUTHOR'].author_family_names
        if inst == [] and 'INSTITUTE' in doc_bib:
            inst = doc_bib['INSTITUTE']
        if rxnf == {} and 'REACTION' in doc_bib:
            rxnf = doc_bib['REACTION']
        if monf is None and 'MONITOR' in doc_bib:
            monf = doc_bib['MONITOR']
        nrxns = 0
        nmons = 0
        if cursor is not None:
            for p in rxnf:
                if verbose:
                    if p == ' ':
                        print('            ' + str(e.accnum) + ', SUBENT: ' + str(snum))
                    else:
                        print('            ' + str(e.accnum) +
                              ', SUBENT: ' + str(snum) + ', pointer:', p)

                # Get the reactions as a list
                meas = rxnf.reactions[p][0]
                if isinstance(meas, exfor_reactions.X4ReactionCombination):
                    rxns = meas.getReactionList()
                elif isinstance(meas, exfor_reactions.X4ReactionIsomerCombination):
                    rxns = meas.getReactionList()
                elif isinstance(meas, exfor_reactions.X4Reaction):
                    rxns = [meas]
                else:
                    raise TypeError('got type ' + str(type(meas)))
                rxn_combo = len(rxns) > 1
                nrxns += len(rxns)

                # Get the monitors as a list
                monitored_rxn = monf is not None and p in monf
                if monitored_rxn:
                    mons = []
                    for rMon in monf.reactions[p]:
                        measMon = rMon[0]
                        if isinstance(measMon, exfor_reactions.X4ReactionCombination):
                            mons += measMon.getReactionList()
                        elif isinstance(measMon, exfor_reactions.X4ReactionIsomerCombination):
                            mons += measMon.getReactionList()
                        elif isinstance(measMon, exfor_reactions.X4Reaction):
                            mons += [measMon]
                        elif measMon is None:
                            pass
                        else:
                            raise TypeError('got type ' + str(type(measMon)))
                    nmons += len(mons)

                if rxn_combo:
                    coupledReactionEntries[(e.accnum, snum, p)] = []
                if monitored_rxn:
                    monitoredReactionEntries[(e.accnum, snum, p)] = []

                # Put the monitors in the monitor pickle and the reaction count pickle
                if monitored_rxn:
                    for mon in mons:

                        # Deal with corner case in MONITOR format rules:
                        # if a MONITOR's quantity is same as the REACTION's, you don't
                        # need to specify it in a MONITOR as it should be understood
                        if mon.quantity == []:
                            mon.quantity = rxnf.reactions[p][0].quantity

                        simpleRxnMon = getSimpleReaction(mon)
                        monitoredReactionEntries[(e.accnum, snum, p)].append(
                            simpleRxnMon.simpleRxn)
                        if simpleRxnMon.simpleRxn not in reactionCount:
                            reactionCount[simpleRxnMon.simpleRxn] = 0
                        reactionCount[simpleRxnMon.simpleRxn] += 1

                        if verbose:
                            print('               ', simpleRxnMon.simpleRxn, '(Monitor)')

                # Put the reactions in the coupled pickle, the reaction count pickle and
                # the index itself
                for r in rxns:
                    simpleRxn = getSimpleReaction(r)
                    if verbose:
                        if rxn_combo:
                            print('               ', simpleRxn.simpleRxn, '(Combo)')
                        else:
                            print('               ', simpleRxn.simpleRxn)
                    for a in auth:
                        #                        print "insert into theworks values(?,?,?,?,?,?,?,?,?) ", \
                        #                            ( e.accnum, snum, p, a, simpleRxn.rtext, simpleRxn.proj, repr(simpleRxn.targ), simpleRxn.quant, rxn_combo, monitored_rxn )
                        cursor.execute("insert into theworks values(?,?,?,?,?,?,?,?,?,?)",
                                       (e.accnum, snum, p, a, simpleRxn.rtext, simpleRxn.proj, simpleRxn.targ, simpleRxn.quant, rxn_combo, monitored_rxn))

                    if simpleRxn.simpleRxn not in reactionCount:
                        reactionCount[simpleRxn.simpleRxn] = 0
                    reactionCount[simpleRxn.simpleRxn] += 1

                    if rxn_combo:
                        coupledReactionEntries[(e.accnum, snum, p)].append(
                            simpleRxn.simpleRxn)
                    if monitored_rxn:
                        monitoredReactionEntries[(e.accnum, snum, p)].append(
                            simpleRxn.simpleRxn)

        if verbose:
            print('           ', "Num. reactions:", nrxns)
            print('           ', "Num. monitors:", nmons)
            print()


# ------------------------------------------------------
#   Error reporting
# ------------------------------------------------------

def reportErrors(outFile, verbose):
    import csv

    f = pickle.load(open(currentErrorFileName, mode='rb'))

    sortedErrors = {}
    for i in f:
        t = type(f[i][0])
        if not t in sortedErrors:
            sortedErrors[t] = []
        sortedErrors[t].append(i)

    # Full report to a csv file
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


def viewErrors(verbose):

    f = pickle.load(open(currentErrorFileName, mode='rb'))

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


# ------------------------------------------------------
#  Main !!
# ------------------------------------------------------
if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Manage the installation & update of x4i's internal copy of the EXFOR database.")
    if True:
        parser.add_argument(
            "-v",
            action="store_true",
            dest='verbose',
            help="Enable verbose output")
        parser.add_argument(
            "-q",
            action="store_false",
            dest='verbose',
            help="Disable verbose output")
        parser.add_argument(
            "-f",
            action="store_true",
            dest='force',
            help="Force overwriting working directories")

        # ------- Control over update actions -------
        parser.add_argument("--build-index", action="store_true", default=False,
                            help="Just (re)builds the sqlite database indexing the EXFOR data in the project. The EXFOR data must be already installed.")
        parser.add_argument("--just-unpack", action="store_true", default=False,
                            help="Just unpack the EXFOR data, then stop.  Do not (re)build the sqlite database index.")

        # # ------- Add (sub)entries -------
        # parser.add_argument("--add-entry", metavar='FILE', type=str, default=None,
        #                     help="Add a single entry x4i's EXFOR database, overwriting an existing one possibly.  Update the index.")
        # parser.add_argument("--add-subentry", metavar='FILE', type=str, default=None,
        #                     help="Add a single subentry x4i's EXFOR database, overwriting an existing one possibly.  Update the index.")
        # parser.add_argument("--add-trans", metavar='TRANS', type=str, default=None,
        #                     help="""Add all the (sub)entries in one IAEA EXFOR transaction and update the index.
        #         The transactions should be zipped, otherwise use the "--add-entry" or "--add-subentry" options.
        # All transactions are available at:
        # http://www-nds.iaea.org/exfor-master/backup/?C=M;O=D""")

        # ------- Remove (sub)entries -------
        parser.add_argument(
            "--remove-entry",
            metavar='ENTRY',
            type=str,
            default=None,
            help="Remove an entry matching this key.")
        parser.add_argument(
            "--remove-subentry",
            metavar='SUBENT',
            type=str,
            default=None,
            help="Remove a subentry matching this key.")

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

        # # ------- Main database loads -------
        # parser.add_argument("--x4c4-master", metavar='ZIPFILE', type=str, default=None,
        #                     help="""Install the (hopefully) IAEA generated X4TOC4 zipfile [zipfile] into the project,
        #         unpack the zipfile, then build the index.
        # The file is available here:
        # http://www-nds.iaea.org/x4toc4-master/?C=M;O=D""")
        parser.add_argument("--exfor-master", metavar='ZIPFILE', type=str, default=None,
                            help="""Install the (hopefully) IAEA generated EXFOR Master File [a zipfile] into the project,
                unpack the zipfile, then build the index.
                The file is available here:  http://www-nds.iaea.org/exfor-master/backup/?C=M;O=D""")

        # ------- Update the EXFOR dicts. -------
        parser.add_argument("--dict", type=str, default=None,
                            help='Reinstall the EXFOR dictionaries using the contents from this IAEA EXFOR dictionary Transaction file.')
        parser.add_argument("--doi", type=str, default=None,
                            help='Reinstall the EXFOR doi <-> entry mapping using the contents from this IAEA EXFOR dictionary text file.')

    args = parser.parse_args()

    # # ------- Add (sub)entries -------
    # if args.add_trans is not None:
    #     raise NotImplementedError()
    # elif args.add_entry is not None:
    #     raise NotImplementedError()
    # elif args.add_subentry is not None:
    #     raise NotImplementedError()

    # # ------- Remove (sub)entries -------
    # elif args.remove_entry is not None:
    #     raise NotImplementedError()
    # elif args.remove_subentry is not None:
    #     raise NotImplementedError()

    # ------- Main database load actions -------
    if args.exfor_master is not None or args.x4c4_master is not None:
        if args.exfor_master is not None:
            unpackEXFORMaster(args.exfor_master, verbose=args.verbose,
                              force=args.force)
        elif args.x4c4_master is not None:
            raise NotImplementedError('X4C4 conversion is implmented but not debugged.')
            # unpackX4C4Master(args.x4c4_master, verbose=args.verbose)
        if not args.just_unpack:
            buildMainIndex(verbose=args.verbose, force=args.force)
            insertDOIIndex(verbose=args.verbose, force=args.force)
    elif args.build_index:
        buildMainIndex(verbose=args.verbose, force=args.force)
        insertDOIIndex(verbose=args.verbose, force=args.force)

    # # ------- Update the EXFOR dicts. -------
    # elif args.dict is not None:
    #     raise NotImplementedError('Building of a dictionary index is not implemented.')
    #     # buildDictionaryIndex(args.dict, verbose=args.verbose, force=args.force)
    elif args.doi is not None:
        insertDOIIndex(verbose=args.verbose, force=args.force)

    # ------- View/save logs -------
    if args.error_log is not None:
        reportErrors(args.error_log, verbose=args.verbose, force=args.force)
    if args.coupled_log is not None:
        raise NotImplementedError()
    if args.view_errors:
        viewErrors(verbose=args.verbose)

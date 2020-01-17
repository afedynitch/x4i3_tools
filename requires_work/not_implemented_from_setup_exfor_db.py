
# def unpackX4C4Master(newZipFile, verbose):
#     '''Unpack an x4c4 master file'''
#     import shutil
#     import subprocess

#     # clean up previous run(s)
#     for xPath in [fullDBPath, DATAPATH + os.sep + 'X4all']:
#         if os.path.exists(xPath):
#             if verbose:
#                 print "Deleting old copy of " + xPath
#             shutil.rmtree(xPath)

#     # move the new file in place
#     shutil.copy(newZipFile, DATAPATH)
#     newZipFile = newZipFile.split(os.sep)[-1]

#     # unpack
#     if verbose:
#         subprocess.check_call(['unzip', newZipFile], cwd=DATAPATH)
#     else:
#         subprocess.check_output(['unzip', newZipFile], cwd=DATAPATH)
#     if not os.path.exists(DATAPATH + os.sep + 'X4all'):
#         raise IOError(
#             "Cannot find file " +
#             DATAPATH +
#             os.sep +
#             'X4all' +
#             ', was the zipfile really a X4C4 master file?  Anyway, you have some cleaning to do in ' +
#             DATAPATH)

#     # rename db (always comes out called "X4all")
#     # if verbose:
#     #     "Renaming " + DATAPATH + os.sep + 'X4all' + " to " + fullDBPath
    # shutil.move(DATAPATH + os.sep + 'X4all', currentDBPath)

    # # make a symlink to the zipfile so everyone knows what the current one is
    # if os.path.exists(fullDBZipFileName):
    #     os.remove(fullDBZipFileName)
    # os.symlink(DATAPATH + os.sep + newZipFile, fullDBZipFileName)


# ------------------------------------------------------
#   Single entry/subentry/transaction management
# ------------------------------------------------------

# Not Implemented Yet
# use exfor_utilities.py's chunkifyX4Request() to split up a TRANS or REQUEST


# ------------------------------------------------------
#  Tools to manage the dictionaries
# ------------------------------------------------------

def buildDictionaryIndex(dictionaryFile, verbose, force):
    raise NotImplementedError()
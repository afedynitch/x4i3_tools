import os
from collections import namedtuple
from multiprocessing import cpu_count

from x4i3 import (
    indexFileName, errorFileName,
    coupledFileName, reactionCountFileName, monitoredFileName,
    dbPath
)

buggyEntries = {}
coupledReactionEntries = {}
monitoredReactionEntries = {}
reactionCount = {}

verbose = False
force = False
nthreads = int(cpu_count()*0.75)

currentIndexFileName = None
currentErrorFileName = None
currentCoupledFileName = None
currentMonitoredFileName = None
currentReactionCountFileName = None
currentDBPath = None

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

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def set_current_dir(master_fname, create=False):
    global currentIndexFileName, currentErrorFileName
    global currentCoupledFileName, currentMonitoredFileName
    global currentReactionCountFileName, currentDBPath

    # Create target directory
    unpackedDir = os.path.splitext(os.path.relpath(master_fname))[0]
    try:
        recreate_dir(unpackedDir, force=False)
    except IOError as err:
        if create:
            recreate_dir(unpackedDir, force=force)
        else:
            pass
    
    new_path = os.path.join('x4i3_' + unpackedDir)

    try:
        recreate_dir(new_path, force=False)
    except IOError as err:
        if create:
            recreate_dir(new_path, force=force)
        else:
            pass

    
    print("set_current_dir(): New files will be stored in", new_path)
    currentIndexFileName = os.path.join(new_path, indexFileName)
    currentErrorFileName = os.path.join(new_path, errorFileName)
    currentCoupledFileName = os.path.join(new_path, coupledFileName)
    currentMonitoredFileName = os.path.join(new_path, monitoredFileName)
    currentReactionCountFileName = os.path.join(new_path, reactionCountFileName)
    currentDBPath = os.path.join(new_path, dbPath)

    return new_path


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


SimpleReaction = namedtuple(
    "SimpleReaction", "proj targ prod rtext quant simpleRxn")
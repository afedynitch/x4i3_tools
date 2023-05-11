# import os
import pathlib
from collections import namedtuple
from multiprocessing import cpu_count

from x4i3 import (
    indexFileName,
    errorFileName,
    coupledFileName,
    reactionCountFileName,
    monitoredFileName,
    dbPath,
)

buggyEntries = {}
coupledReactionEntries = {}
monitoredReactionEntries = {}
reactionCount = {}

verbose = False
force = False
nthreads = int(cpu_count() * 0.75)

currentIndexFileName = None
currentErrorFileName = None
currentCoupledFileName = None
currentMonitoredFileName = None
currentReactionCountFileName = None
currentDBPath = None


def recreate_dir(path, force):
    import shutil

    path = pathlib.Path(path)
    # if force and path.exists():
    #     shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=True)


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def set_current_dir(master_file, create=False):
    global currentIndexFileName, currentErrorFileName
    global currentCoupledFileName, currentMonitoredFileName
    global currentReactionCountFileName, currentDBPath

    # Create target directory
    master_file = pathlib.Path(master_file)
    basedir = master_file.parent.absolute()
    tag = master_file.stem.replace("EXFOR", "X4")
    print("tag", tag)
    unpacked_dir = basedir / ("unpack_" + master_file.stem)
    x4i3_db_dir = unpacked_dir / tag

    recreate_dir(unpacked_dir, force=force or create)
    recreate_dir(x4i3_db_dir, force=force or create)

    print("set_current_dir(): Database will be unpacked to", x4i3_db_dir)
    currentIndexFileName = x4i3_db_dir / indexFileName
    currentErrorFileName = x4i3_db_dir / errorFileName
    currentCoupledFileName = x4i3_db_dir / coupledFileName
    currentMonitoredFileName = x4i3_db_dir / monitoredFileName
    currentReactionCountFileName = x4i3_db_dir / reactionCountFileName
    currentDBPath = x4i3_db_dir / dbPath

    # Create tag file
    pathlib.Path(x4i3_db_dir / tag).touch(exist_ok=True)

    return unpacked_dir, x4i3_db_dir


def getQuantity(quantList):
    """
    Most quantities are the 1st ones in the quantity list
    ... but there are a lot of important exceptions ...
    ... 'POT' is the exceptions to the exceptions ...
    """
    for q in [
        "AA",
        "AKE/DA",
        "AKE",
        "AMP",
        "AP",
        "AP/DA",
        "COR",
        "COR/DE",
        "CRL",
        "DA/RAT",
        "DA",
        "DA/DE",
        "DA/DP",
        "DA/CRL",
        "DA/DA",
        "DA/DA/DE",
        "DA/DE",
        "DA/KE",
        "DA/TMP",
        "DE",
        "FM/DA",
        "FY",
        "FY/DE",
        "FY/RAT",
        "FY/SUM",
        "FY/CRL",
        "INT",
        "INT/DA",
        "ISP",
        "KE",
        "KE/CRL",
        "MCO",
        "MLT",
        "NU",
        "NU/DE",
        "POL",
        "POL/DA/DE",
        "POL/DA",
        "POL/DA/DA/DE",
        "RI",
        "SPC",
        "SPC/DMT/DR",
        "SPC/DPT/DR",
        "SPC/DR",
        "PY",
        "SIG",
        "SIG/RAT",
        "SIG/SUM",
        "TTY",
        "TTY/DA/DE",
        "TTY/DA",
        "WID",
        "WID/RED",
        "WID/STR",
        "ZP",
    ]:
        if q in quantList:
            return q
    if "POT" in quantList:
        return "POT"
    return quantList[0]


SimpleReaction = namedtuple("SimpleReaction", "proj targ prod rtext quant simpleRxn")

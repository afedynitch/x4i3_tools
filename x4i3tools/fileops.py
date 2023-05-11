import os


def write_entries_to_file(args):
    dbPath, entries = args

    nfiles_written = 0
    for entry in entries:
        for line in entry:
            if "ENTRY" in line:
                entryNum = line[17:22]
                break
        newX4Path = os.path.join(dbPath, entryNum[0:3])

        try:
            os.makedirs(newX4Path)
        except FileExistsError:
            pass

        newX4File = entryNum + ".x4"
        open(os.path.join(newX4Path, newX4File), mode="w").writelines("".join(entry))
        nfiles_written += 1

    return nfiles_written


def unpackEXFORMaster(master_fname):
    """Unpack an EXFOR master file"""
    import zipfile
    import x4i3.exfor_utilities
    import x4i3tools as x4t
    from tqdm import tqdm
    from multiprocessing import Pool

    unpackedDir = x4t.set_current_dir(master_fname)[0]

    if x4t.verbose:
        print("Unpacking master file: ", master_fname)
    with zipfile.ZipFile(master_fname, "r") as zip_ref:
        zip_ref.extractall(unpackedDir)

    nfiles_written = 0
    # repackage the file
    backupFile = list(unpackedDir.glob("*.bck"))[0]
    theLines = open(backupFile, mode="r").readlines()
    entries = x4i3.exfor_utilities.chunkifyX4Request(theLines)
    workpackages = [(x4t.currentDBPath, entries) for entries in x4t.chunks(entries, 30)]
    with Pool(x4t.nthreads) as mpool:
        processed = list(
            tqdm(
                mpool.imap(write_entries_to_file, workpackages), total=len(workpackages)
            )
        )
    nfiles_written = sum(processed)

    print("In total", nfiles_written, "have been extracted.")

    # cleanup
    # shutil.rmtree(unpackedDir)


def unpackX4Master(master_fname):
    """Unpack an X4 master file."""
    import zipfile
    import x4i3tools

    unpackedDir = x4i3tools.set_current_dir(master_fname)[0]

    if x4i3tools.verbose:
        print("Unpacking master file: ", master_fname)
    with zipfile.ZipFile(master_fname, "r") as zip_ref:
        zip_ref.extractall(unpackedDir)

    x4i3tools.currentDBPath = os.path.join(unpackedDir, "X4all")

import os
from posixpath import abspath


def process_file_package(work_package):
    import pyparsing
    from x4i3 import exfor_exceptions
    from x4i3tools.entry_generators import processEntry

    dbPath, file_list = work_package

    thr_coupledReactionEntries = {}
    thr_monitoredReactionEntries = {}
    thr_reactionCount = {}
    thr_sql_transactions = []
    thr_buggyEntries = {}

    for f in file_list:
        try:
            processEntry(
                f,
                thr_sql_transactions,
                thr_coupledReactionEntries,
                thr_monitoredReactionEntries,
                thr_reactionCount,
                dbPath,
            )
        except (
            exfor_exceptions.IsomerMathParsingError,
            exfor_exceptions.ReferenceParsingError,
            exfor_exceptions.ParticleParsingError,
            exfor_exceptions.AuthorParsingError,
            exfor_exceptions.InstituteParsingError,
            exfor_exceptions.ReactionParsingError,
            exfor_exceptions.BrokenNumberError,
        ) as err:
            thr_buggyEntries[f] = (err, str(err))
            continue
        except (Exception, pyparsing.ParseException) as err:
            thr_buggyEntries[f] = (err, str(err))
            continue

    return (
        thr_coupledReactionEntries,
        thr_monitoredReactionEntries,
        thr_reactionCount,
        thr_sql_transactions,
        thr_buggyEntries,
    )


def buildMainIndex():
    """
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

    """
    import glob
    import pickle
    import pprint
    import random
    import sqlite3
    from tqdm import tqdm

    from multiprocessing import Pool

    import pyparsing
    from x4i3 import exfor_exceptions
    import x4i3tools as x4t

    def remove_if_force(file_name):
        if os.path.exists(file_name) and x4t.force:
            os.remove(file_name)
        elif os.path.exists(file_name):
            raise IOError(
                "Can not overwrite file", file_name, "Consider using -f (force) flag."
            )

    # clean up previous runs
    remove_if_force(x4t.currentIndexFileName)
    remove_if_force(x4t.currentErrorFileName)
    remove_if_force(x4t.currentCoupledFileName)
    remove_if_force(x4t.currentReactionCountFileName)
    remove_if_force(x4t.currentMonitoredFileName)

    # build up the table
    if x4t.verbose:
        print(x4t.currentDBPath.glob("**/*.x4"))

    files_to_process = list(x4t.currentDBPath.glob("**/*.x4"))
    total_files = len(files_to_process)
    chunksize = min(total_files // x4t.nthreads, 50)
    print(x4t.currentDBPath, total_files)
    assert total_files > 0, "No files found in " + x4t.currentDBPath.name

    if x4t.verbose:
        print(
            "Will process {0} files in chunks of {1} using {2} threads.".format(
                total_files, chunksize, x4t.nthreads
            )
        )

    # Shuffle the list to balance the work per thread
    # random.shuffle(files_to_process)
    workpackages = []
    for chunk in x4t.chunks(files_to_process, chunksize):
        workpackages.append((x4t.currentDBPath, chunk))
    print("Workpackages: ", len(workpackages))
    with Pool(x4t.nthreads) as mpool:
        processed = list(
            tqdm(
                mpool.imap(process_file_package, workpackages), total=len(workpackages)
            )
        )
        # processed = mpool.map(generate_entries_threads, workpackages)

    coupledReactionEntries = {}
    monitoredReactionEntries = {}
    reactionCount = {}
    sql_transactions = []
    buggyEntries = {}

    for wp in tqdm(processed):
        (
            wp_coupledReactionEntries,
            wp_monitoredReactionEntries,
            wp_reactionCount,
            wp_sql_transactions,
            wp_buggyEntries,
        ) = wp
        coupledReactionEntries.update(wp_coupledReactionEntries)
        monitoredReactionEntries.update(wp_monitoredReactionEntries)
        reactionCount.update(wp_reactionCount)
        buggyEntries.update(wp_buggyEntries)
        sql_transactions += wp_sql_transactions

    print("Files processed: ", total_files)
    print("Lenths:")
    print("\tNumber of entries with coupled data sets:", len(coupledReactionEntries))
    print(
        "\tNumber of entries with reaction monitors sets:",
        len(monitoredReactionEntries),
    )
    print("\tNumber of distinct reactions:", len(reactionCount))
    print("\tsql_transactions:", len(sql_transactions))
    print("\tErroneous entries:", len(buggyEntries))
    if x4t.verbose and len(buggyEntries) > 0:
        pprint.pprint(buggyEntries)

    pickle.dump(coupledReactionEntries, open(x4t.currentCoupledFileName, mode="wb"))
    pickle.dump(monitoredReactionEntries, open(x4t.currentMonitoredFileName, mode="wb"))
    pickle.dump(reactionCount, open(x4t.currentReactionCountFileName, mode="wb"))
    pickle.dump(buggyEntries, open(x4t.currentErrorFileName, mode="wb"))

    # set up database & create the table
    connection = sqlite3.connect(x4t.currentIndexFileName)  # pylint: disable=no-member
    cursor = connection.cursor()
    cursor.execute(
        """create table if not exists theworks (entry text, subent text, pointer text, author text, reaction text, projectile text, target text, quantity text, rxncombo bool, monitored bool)"""
    )

    # Write all sql_entries to the database in one transaction
    # cursor.execute('BEGIN TRANSACTION')
    cursor.executemany(
        "insert into theworks values(?,?,?,?,?,?,?,?,?,?)", sql_transactions
    )
    # cursor.execute('COMMIT')

    # # commit & close connection to database
    connection.commit()
    cursor.close()


def insertDOIIndex(doiFileName="x4doi.txt"):
    """
    Adds the DOI cross reference table to the main index.
    The IAEA should probably tightly associated this data with
    the EXFOR data, but for some reason it is not.
    """
    import sqlite3
    import x4i3tools as x4t

    try:
        print("Inserting DOI info from", doiFileName, "in", x4t.currentIndexFileName)
    except NameError as err:
        print("Current files not defined", err)
        exit()
    if not os.path.exists(doiFileName):
        raise IOError("DOi file not found")
    # set up database & create the table
    connection = sqlite3.connect(x4t.currentIndexFileName)  # pylint: disable=no-member
    cursor = connection.cursor()
    cursor.execute("""drop table if exists doiXref""")
    cursor.execute(
        """create table doiXref (entry text, nsr text, doi text, reference text )"""
    )

    for line in open(doiFileName).readlines():
        entry = line[32:46].strip().replace("$ENTRY=", "")
        nsr = line[46:61].strip().replace("$NSR=", "")
        doi = line[61:].strip().replace("$DOI=", "")
        reference = line[0:32].strip().replace("$REF=", "")
        cursor.execute(
            "insert into doiXref values(?,?,?,?)", (entry, nsr, doi, reference)
        )

    # commit & close connection to database
    connection.commit()
    cursor.close()

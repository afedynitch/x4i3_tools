

def getSimpleReaction(complicatedReaction):
    from x4i3tools import SimpleReaction, getQuantity
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


def processEntry(entryFileName, sqlTransactions, coupledReactionEntries,
                 monitoredReactionEntries, reactionCount, dbPath):
    '''
    Computes the rows for a single entry and puts it in the database
    '''
    import os
    import x4i3tools as x4t
    import x4i3
    from x4i3 import exfor_entry, exfor_reactions

    if x4t.verbose:
        print('        ', os.path.split(entryFileName)[1], end=' ')
    
    this_entry = exfor_entry.x4EntryFactory(
        entryFileName.split(os.sep)[-1].split('.')[0],
        customDBPath=dbPath
    )
    
    doc_bib = this_entry[1]['BIB']
    try:
        m = this_entry.meta().legend()
        if x4t.verbose:
            print(str(this_entry.accnum) + ':', m)
    except Exception:
        m = None
        print()
    auth = []  # author field
    inst = []  # institute field
    if 'AUTHOR' in doc_bib:
        auth = doc_bib['AUTHOR'].author_family_names
    if 'INSTITUTE' in doc_bib:
        inst = doc_bib['INSTITUTE']
    if x4t.verbose:
        print('        ', "Num. authors:", len(auth))
        print('        ', "Num. institutes:", len(inst))
        print()

    for snum in this_entry.sortedKeys()[1:]:
        rxnf = {}  # reaction field
        monf = None  # monitor field
        if 'BIB' in this_entry[snum]:
            bib = this_entry[snum]['BIB']
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
        # if cursor is not None:

        for p in rxnf:
            if x4t.verbose:
                if p == ' ':
                    print('            ' + str(this_entry.accnum) + ', SUBENT: ' + str(snum))
                else:
                    print('            ' + str(this_entry.accnum) +
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
                coupledReactionEntries[(this_entry.accnum, snum, p)] = []
            if monitored_rxn:
                monitoredReactionEntries[(this_entry.accnum, snum, p)] = []

            # Put the monitors in the monitor pickle and the reaction count pickle
            if monitored_rxn:
                for mon in mons:

                    # Deal with corner case in MONITOR format rules:
                    # if a MONITOR's quantity is same as the REACTION's, you don't
                    # need to specify it in a MONITOR as it should be understood
                    if mon.quantity == []:
                        mon.quantity = rxnf.reactions[p][0].quantity

                    simpleRxnMon = getSimpleReaction(mon)
                    monitoredReactionEntries[(this_entry.accnum, snum, p)].append(
                        simpleRxnMon.simpleRxn)
                    if simpleRxnMon.simpleRxn not in reactionCount:
                        reactionCount[simpleRxnMon.simpleRxn] = 0
                    reactionCount[simpleRxnMon.simpleRxn] += 1

                    if x4t.verbose:
                        print('               ', simpleRxnMon.simpleRxn, '(Monitor)')

            # Put the reactions in the coupled pickle, the reaction count pickle and
            # the index itself
            for r in rxns:
                simpleRxn = getSimpleReaction(r)
                if x4t.verbose:
                    if rxn_combo:
                        print('               ', simpleRxn.simpleRxn, '(Combo)')
                    else:
                        print('               ', simpleRxn.simpleRxn)
                for a in auth:
                    #                        print "insert into theworks values(?,?,?,?,?,?,?,?,?) ", \
                    #                            ( e.accnum, snum, p, a, simpleRxn.rtext, simpleRxn.proj, repr(simpleRxn.targ), simpleRxn.quant, rxn_combo, monitored_rxn )
                    sqlTransactions.append(
                         (this_entry.accnum, snum, p, a, simpleRxn.rtext, simpleRxn.proj,
                          simpleRxn.targ, simpleRxn.quant, rxn_combo, monitored_rxn)
                    )
                    # cursor.execute(

                if simpleRxn.simpleRxn not in reactionCount:
                    reactionCount[simpleRxn.simpleRxn] = 0
                reactionCount[simpleRxn.simpleRxn] += 1

                if rxn_combo:
                    coupledReactionEntries[(this_entry.accnum, snum, p)].append(
                        simpleRxn.simpleRxn)
                if monitored_rxn:
                    monitoredReactionEntries[(this_entry.accnum, snum, p)].append(
                        simpleRxn.simpleRxn)

        if x4t.verbose:
            print('           ', "Num. reactions:", nrxns)
            print('           ', "Num. monitors:", nmons)
            print()

#! /usr/bin/env python

import sys, os, argparse, cPickle, collections, subprocess, copy
from x4i3 import __path__, abundance, endl_Z, fullMonitoredFileName, fullCoupledFileName
from x4i.exfor_utilities import unique

# -----------------------------------------------------------------------
#    Global data
# -----------------------------------------------------------------------

DATAPATH            = os.sep.join( __path__ + [ 'data' ] )
coupledFileName     = 'coupled-entries.pickle'
fullCoupledFileName = DATAPATH + os.sep + coupledFileName

dot_template = '''
graph G  {
	center=""
	node[width=.25,height=.375,fontsize=9]
#CONNECTIONS
#CLUSTERS
#SPECIALNODESETTINGS
}
'''
graphml_template = '''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<graphml xmlns="http://graphml.graphdrawing.org/xmlns" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:y="http://www.yworks.com/xml/graphml" xmlns:yed="http://www.yworks.com/xml/yed/3" xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns http://www.yworks.com/xml/schema/graphml/1.1/ygraphml.xsd">
  <key for="node" id="d6" yfiles.type="nodegraphics"/>
  <key for="edge" id="d10" yfiles.type="edgegraphics"/>
  <graph edgedefault="undirected" id="G">
    #NODES
    #EDGES
    #CLUSTERS
  </graph>
</graphml>
'''

#ENDF/B-VI standards, all SIG
standards = '''H-1(N,EL)
HE-3(N,P)
LI-6(N,T)
LI-6(N,EL)
B-10(N,A+G)
B-10(N,A)
B-10(N,EL)
C-0(N,EL)
AU-197(N,G)
U-235(N,F)
U-238(N,F)
PU-239(N,F)'''.split()

# List of all the EXFOR connected sets encountered
allTheEXFORConnectedSets = []
EXFORConnectedSet = collections.namedtuple( "EXFORConnectedSet", "entry subent ptr reactionEquation reactions" )

colorMap = {\
    'black':'#000000',\
    'white':'#FFFFFF',\
    'dark blue':'#003399',\
    'light blue':'#E8EEF7',\
    'yellow':'#FFFF99',\
    'green':'#98BF21'}

# -----------------------------------------------------------------------
#    Class definitions
# -----------------------------------------------------------------------

# ---------------- simple structs ----------------

Connection = collections.namedtuple( "Connection", "fr to color" )

ConnectionFormat = None

NodeFormat = collections.namedtuple( "NodeFormat", "label color fillcolor fontcolor" ) #shape height width fontsize" )

# ---------------- actual classes ----------------

class RenderedObject: 
    def __init__(self, x):
        if type(x) in [ list, tuple ]: self.x = tuple( [ y.replace("']",'') for y in x ] )
        else:                          self.x = x
    def __str__( self ): 
        return str(self.x)

class Projectile(RenderedObject): 
    def __str__( self ): 
        if self.x == 'HE3': return 'He-3'
        return self.x.lower( )

class Compound(RenderedObject): 
    def __str__( self ): 
        tmp = self.x.split('-')
        return tmp[0].capitalize( )+'-'+'-'.join( tmp[1:] )

class Nucleus(RenderedObject):
    def __str__( self ): 
        if self.x.count('-') == 1: return self.x.capitalize( )
        if self.x == '0-G-0': return 'g'
        if self.x.count( '-' ) == 3: 
            tmp = self.x.split('-')[1:]
            return (tmp[0]+'-'+tmp[1]+tmp[2]).capitalize()
        if 'M' in self.x[-2:]:
            tmp = self.x.split('-')
            return (tmp[0]+'-'+tmp[1]+tmp[2]).capitalize()
        tmp = self.x.split('-')[1:]
        return (tmp[0]+'-'+tmp[1]).capitalize()

class UnspecifiedParticle(RenderedObject): 
    def __str__( self ): 
        if self.x in [ 'X', 'ELEM', 'MASS', 'ELEM/MASS' ]: return self.x
        return self.x.lower( )

def parseParticle( x ):
    if 'CMP' in x: return Compound( x )
    elif '-' in x: return Nucleus( x )
    elif x in [ 'N', 'P', 'G', 'A', 'T', 'D', 'HE3' ]: return Projectile( x )
    else: return UnspecifiedParticle( x )

class Reaction(RenderedObject): 
    def __init__(self, x):
        RenderedObject.__init__( self, x )
        self.targ  = parseParticle( self.x.split('(')[0] )
        self.proj  = parseParticle( self.x.split('(')[1].split(',')[0] )
        self.prods = [ parseParticle( p ) for p in self.x.split('(')[1].split(',')[1].rstrip(')').split('+') ]
    def __str__( self ): 
        return str(self.targ)+'('+str(self.proj)+','+'+'.join( [ str(p) for p in self.prods ] ) +')'

class Node(RenderedObject):
    def __init__(self, x ):
        RenderedObject.__init__( self, x )
        self.quant = self.x[1]
        if self.quant == '': self.obj = parseParticle( self.x[0] )
        else:                self.obj = Reaction( self.x[0] )
    def __str__( self ):
        if self.quant == '': return str(self.obj)
        else:                return str(self.obj)+"\n"+self.quant 

class Graph:
    def __init__(self):
        '''
        Nodes are a tuple of the form: (name, quantity) where quantity  is either '' for 
        a target node or something like 'SIG' for actual data.  There are several types of 
        nodes in the graph ::
            
            * isotopic targets
            * elemental targets
            * regular reactions
            * standards evaluation reactions
        
        Connections are tuples of the form ( fromNode, toNode ).  There are also several 
        types of connections in the graph ::
            
            * isotope <-> element
            * isotope <-> reaction (regular or standards)
            * element <-> reaction (   "    or    "     )
            * reaction <-> reaction for coupled data
            * reaction <-> reaction used as a monitor

        The Connections and Nodes are stored in a few data structures ::

            * connectionMap : a map of nodes of the form { clusterID: [ node list ] }.  
              The cluster id is the quantity described in the node and is either '' for a 
              target node or something like 'SIG' for actual data.
            * clusterMap : a map of connections of the form { ( toNode, fromNode ): number Links }
            * specialNodeList : list of nodes to receive special markup -- use this for 
              standards evaluation nodes
            * linkedElementNodeList : list of nodes corresponding to elements whose links 
              have been generated when the "elemental_data_is_coupled" switch is activated
        
        Connection statistics ::

            * numRxnRxnLinks : the number of reaction <-> reaction links (for coupled data)
            * numRxnMonLinks : the number of reaction <-> reaction links (for reactions used as monitors)
            * numRxnTargLinks : the number of isotope <-> reaction + element <-> reaction links
            * numTargNodes : the number of isotope + element nodes
            * numElemNodes : the number of element nodes
            * numRxnNodes : the number of reaction nodes of all types
            * numStandardsRxnNodes : the number of standards reaction nodes

        '''
        # Compute the connections
        self.connectionMap = {}
        self.clusterMap = {}
        self.specialNodeList = []
        self.linkedElementNodeList = []
        # Connection statistics
        self.numRxnRxnLinks = 0
        self.numRxnMonLinks = 0
        self.numRxnTargLinks = 0
        self.numTargNodes = 0
        self.numElemNodes = 0
        self.numRxnNodes = 0
        self.numStandardsRxnNodes = 0
    
    
    def addNode( self, n, verbose = False ):
        '''
        Adds requested node to the clusterMap.  Take statistics.
        '''
        # If node type not registered in clusterMap, register it
        if n[1] not in self.clusterMap: self.clusterMap[ n[1] ] = []

        # Is this a new node, or did we do it already?
        if n not in self.clusterMap[ n[1] ]: 
            
            # Check if the node is valid and update statistics
            if n[1] == '':
                if '-0' in n[0]: 
                    if not hasElemental( n[0] ): raise ValueError( str(n[0])+" does not exist as an element" )
                    self.numTargNodes += 1
                    self.numElemNodes += 1
                    if verbose: print '    Element:',n[0]
                else:
                    self.numTargNodes += 1
                    if verbose: print '    Isotope:',n[0]
            else:
                self.numRxnNodes += 1
                if verbose: print '    Reaction:',n[0]
                # Special Reaction Nodes (standards...)
                if n[0] in standards and n[1] == 'SIG' and not n in self.specialNodeList: 
                    self.numStandardsRxnNodes += 1
                    self.specialNodeList.append( n )
                    if verbose: print '        ** standard'
            
            # Node is valid, so register it in the clusterMap list for it's type
            self.clusterMap[ n[1] ].append( n )
    
    
    def addLink( self, n0, n1, verbose = False, monitor=False ):
        '''
        Adds requested link to the connectionMap. Take statistics.
        '''
        if n0 == n1: return
        
        # Register the link
        if monitor: c = Connection( fr=n0, to=n1, color='dark blue' )
        else:       c = Connection( fr=n0, to=n1, color='black' )
        if not c in self.connectionMap: self.connectionMap[c] = 1
        else:                           self.connectionMap[c] += 1
        
        # Statistics on the links
        if '' in [ n0[1], n1[1] ] :
            if n0[1] != n1[1]: self.numRxnTargLinks += 1
        else:
            self.numRxnRxnLinks += 1        
 

    def addNodesAndLinks( self, n0, n1, coupledOnly = False, include_elem_to_iso = False, elemental_data_is_coupled = False, verbose = False, monitor=False ):
        '''
        Adds all the relevant nodes and links for n0 and n1.  The nodes
        n0 and n1 are assumed to be reaction nodes derived from x4i's coupled data file.
        We will add (depending on options) ::
        
            * Always ::
            
                * connection between reactions n0 and n1
            
            * If coupledOnly == False ::

                * connection between reaction n0 and the target of reaction n0
                * connection between reaction n1 and the target of reaction n1
                
                * If either include_elem_to_iso or elemental_data_is_coupled == True ::

                    * connection between target of reaction n0 and corresponding element
                    * connection between target of reaction n1 and corresponding element
                    
                * If elemental_data_is_coupled == True, the code queries for all EXFOR data 
                  on the pure elemental targets corresponding to n0 and n1 then adds the 
                  follow links ::
                  
                    * connections between n0's corresponding element and elemental reaction data
                    * connections between n1's corresponding element and elemental reaction data
        '''    
        if '' in [ n0[1], n1[1] ]: raise ValueError( "One of the nodes is not a valid reaction: " + str( n0 ) + ' and ' + str( n1 ) )
        
        # Now add the reaction nodes and the reaction -- reaction link
        self.addNode( n0, verbose )
        self.addNode( n1, verbose )
        self.addLink( n0, n1, verbose, monitor=monitor )

        # Ah.. and expanded view of coupled data:
        if not coupledOnly:
            for n in [ n0, n1 ]:
            
                # The target -- reaction link and the target node
                targNode = ( str( Reaction(n[0]).targ ), '' )
                self.addNode( targNode, verbose )
                self.addLink( targNode, n )
                
                # Now for elemental stuff
                if targNode[0].endswith( '-0' ): elemNode = targNode
                else: elemNode = ( targNode[0].split('-')[0]+'-0', '' )
                if ( include_elem_to_iso or elemental_data_is_coupled ) and hasElemental( elemNode[0] ):
                    
                    # Have to add element node & element to isotope couplings
                    self.addNode( elemNode )
                    if include_elem_to_iso or elemental_data_is_coupled: self.addLink( elemNode, targNode )
                    
                    # Now look up all elemental data and add it too
                    if elemental_data_is_coupled:
                        theQuery = ( elemNode[0], str(Reaction(n[0]).proj), n[1] )
                        if not theQuery in self.linkedElementNodeList: 
                            self.linkedElementNodeList.append( theQuery )
                            queryMap = db.query( target = theQuery[0], projectile = theQuery[1], quantity = theQuery[2] )
                            for k in queryMap:
                                theEntry = exfor_entry.X4Entry( db.retrieve( ENTRY=k )[ k ] )
                                for subent in queryMap[k]:
                                    if subent.endswith( '001' ): continue
                                    theReactionField = theEntry[ subent ]['BIB'][ 'REACTION' ]
                                    for rxn in theReactionField.reactions:
                                        if not isinstance( theReactionField.reactions[rxn][0], exfor_reactions.X4Reaction ):
                                            #if verbose: print "Already did:",\
                                            #    theReactionField.reactions[rxn][0].__class__,":", theReactionField.reactions[rxn][0]
                                            continue
                                        elemRxnNode = ( str( Reaction(exfor_reactions.X4Process.__repr__( theReactionField.reactions[rxn][0] )) ), n[1] )        
                                        self.addNode( elemRxnNode, verbose )
                                        self.addLink( elemRxnNode, elemNode )
                                        allTheEXFORConnectedSets.append( EXFORConnectedSet( k, subent, rxn, 'element', [ elemRxnNode ] ) )
        

    def printStatistics( self ):
        print "Graph statistics:"
        print     '           # reaction-reaction links:', self.numRxnRxnLinks
        print     '             # reaction-target links:', self.numRxnTargLinks
        print     '                      # target nodes:', self.numTargNodes
        print     '    # target nodes that are elements:', self.numElemNodes
        print     '                    # reaction nodes:', self.numRxnNodes
        print     '          # standards reaction nodes:', self.numStandardsRxnNodes #, len( self.specialNodeList )
        print     '                  len(connectionMap):', len( self.connectionMap )


# Special formatting for Nodes
def decorateNode( x, numNodes=1 ): 
    '''
    Decorate nodes ::
        
        * regular reactions are rectangles
        * standards evaluation reactions are dark blue rectangles
        * isotopes are ovals
        * elements are green ovals
    '''
    fillcolor=colorMap['light blue']    #'#E8EEF7'
    bordercolor=colorMap['black']       #'#000000'
    fontcolor=colorMap['black']         #'#000000'
    shape="rectangle" 
    # For standards reaction nodes
    if x[0] in standards and x[1] == 'SIG':
        fillcolor=colorMap['dark blue'] #'#003399'
        bordercolor=colorMap['white']   #'#FFFFFF'
        fontcolor=colorMap['white']     #'#FFFFFF'
    # For target (e.g. isotopes) nodes
    if x[1] == '':
        if '-0' in x[0]: fillcolor=colorMap['green']    #'#98BF21'
        else: fillcolor=colorMap['yellow']              #'#FFFF99'
        shape = "circle"
    nodeId = 'n'+str(hash(x))
    return '''
    <node id ="%(nodeId)s">
        <data key="d6">
            <y:ShapeNode>
                <y:Geometry x="891.75" y="767.0"/>
                <y:Fill color="%(fillcolor)s" transparent="false"/>
                <y:BorderStyle color="%(bordercolor)s" type="line" width="1.0"/>
                <y:NodeLabel alignment="center" autoSizePolicy="content" textColor="%(fontcolor)s" visible="true">%(nodeLabelText)s</y:NodeLabel>
                <y:Shape type="%(shape)s"/>
                <y:DropShadow color="#00000040" offsetX="5" offsetY="5"/>
            </y:ShapeNode>
        </data>
    </node>
    ''' % { 'fillcolor':fillcolor, 'bordercolor':bordercolor, 'fontcolor':fontcolor, 'shape':shape, 'nodeLabelText':str(Node(x)), 'nodeId':nodeId }


# Special formatting for Edges
def decorateEdge( x, y, edgeStyle=None, edgeColor='black', numConnections=1 ): 
    '''
    Represent connections between observables and targets ::
    
        * reaction -- reaction connections are solid and black
        * reaction -- monitor connections are solid and dark blue
        * reaction -- target connections are dashed
        * isotope -- element connections are dotted and green
    '''
    if edgeStyle == None: 
        if '' in [ x[1], y[1] ]: 
            if x[1] == y[1]: edgeStyle='dotted'
            else: edgeStyle="dashed"
        else: edgeStyle="solid"
    xNodeId = 'n'+str(hash(x))
    yNodeId = 'n'+str(hash(y))
    nodeId  = 'e'+str(hash(x)+hash(y))
    if edgeStyle != None:
        return '''
        <edge id="%(nodeId)s" source="%(xNodeId)s" target="%(yNodeId)s">
            <data key="d10">
                <y:PolyLineEdge>
                    <y:Path sx="0.0" sy="0.0" tx="0.0" ty="0.0"/>
                    <y:LineStyle color="%(edgeColor)s" type="%(edgeStyle)s" width="%(edgeWidth)f"/>
                    <y:Arrows source="none" target="none"/>
                    <y:BendStyle smoothed="false"/>
                </y:PolyLineEdge>
            </data>
        </edge>''' % { \
            'nodeId':nodeId, 'xNodeId':xNodeId, 'yNodeId':yNodeId, \
            'edgeStyle':edgeStyle, 'edgeColor':colorMap[ edgeColor ], \
            'edgeWidth':2.0*numConnections }
    return '<edge id="'+nodeId+'" source="'+xNodeId+'" target="'+yNodeId+'"/>'


def hasElemental( targ ):
    '''
    Returns true if target is or is part of a naturally occurring element, on Earth.
    '''
    sym = targ.split('-')[0]
    if len(sym) != 1: sym = sym.capitalize()
    Z = endl_Z.endl_SymbolZ( sym )
    for za in abundance.abundances:
        if za[0] == Z: return True
    return False

def addElementsIsotopes( targList ):
    '''
    Scans the targList for elements (of form "Sym-0")
    and adds all the isotopes for "Sym-0" to the targList.
    This routine does not check if elements encountered are 
    valid, in that they actually occur naturally on Earth.
    '''
    result = copy.copy( targList )
    for targ in targList:
        if targ.endswith( '-0' ):
            sym = targ.split('-')[0]
            Z = endl_Z.endl_SymbolZ( sym )
            for za in abundance.abundances:
                if za[0] == Z: 
                    newIso = sym.capitalize()+'-'+str(za[1])
                    if newIso not in result: 
                        result.append( newIso )
    return result

# -----------------------------------------------------------------------
#    Command line parsing
# -----------------------------------------------------------------------

def process_args():
    parser = argparse.ArgumentParser(description = 'Visualize coupled datasets in the EXFOR library using GraphViz')
    parser.set_defaults( verbose = False )
    parser.add_argument("-v", action="store_true", dest='verbose', help="enable verbose output")
    parser.add_argument("-q", action="store_false", dest='verbose', help="disable verbose output")
    parser.add_argument("-i", default=fullCoupledFileName, dest="inFile", type=str, help="Coupled data pickle file containing information on all coupled EXFOR data sets [default: "+fullCoupledFileName+"]" )
    parser.add_argument("-m", default=fullMonitoredFileName, dest="monFile", type=str, help="Monitor data pickle file containing information on all monitor reactions in EXFOR [default: "+fullMonitoredFileName+"]" )
    parser.add_argument("-T", default='graphml', dest='format', type=str, choices = [ 'gv', 'ps', 'png', 'svg', 'pdf', 'jpg', 'gif', 'eps', 'fig', 'gtk', 'graphml' ], help="Output format for graph [Default: 'graphml']" ) 
    parser.add_argument("--borders", default=False, action='store_true', help="attempt to draw borders around clusters" )
    parser.add_argument('--renderer', default='dot', dest='renderer', type=str, choices = [ 'dot', 'neato', 'fdp', 'sfdp', 'twopi', 'circo', 'osage' ], help="GraphViz renderer for types other then 'gv' [Default: dot]" ) 
    parser.add_argument('--neutron-only', default=False, action='store_true', help="only show neutron incident reaction data" )
    parser.add_argument('--xsect-only', default=False, action='store_true', help='only show cross section ("SIG") data' )
    parser.add_argument('--coupled-only', default=False, action='store_true', help="only show coupled reaction data, suppress plotting the nucleus nodes" )
    parser.add_argument('--include-elem-to-iso', default=False, action='store_true', help="include the isotopic to element coupling for elemental data.  Any isotopes not on your list that make up an element will be added to list." )
    parser.add_argument('--elemental-data-is-coupled', default=False, action='store_true', help="any simple reactions on an elemental target will be considered as coupled data for the isotopes that compose the element and will be shown on the graph" )
    parser.add_argument('--stats', default=False, action='store_true', help="print node/link statistics" )
    parser.add_argument("--filterFile", default=None, type=str, help="file containing filters on project, target and observable" )
    parser.add_argument("--connectedSetsFile", default=None, type=str, help="file to output all the connected sets (if supplied)" )
    parser.add_argument("outFilePrefix", type=str, help="the prefix of the output files")
    return parser.parse_args()


# -----------------------------------------------------------------------
#    Main routine
# -----------------------------------------------------------------------

if __name__ == "__main__":
    '''
    The pickle file is just a python dictionary with the following structure:
    
        ``coupledReactionEntries[ ( e.accnum, snum, p ) ].append( ( targ + '(' + rtext + ')', quant ) )``
    
    In other words :: 
    
        * The data in the coupled data file are stored in a map: { EXFORTuple:[ data set list ] }
        * The EXFOR tuple is of the form ( ENTRY, SUBENTRY, POINTER ) where POINTER may be ' ' or a number.
        * Each set in the data set list consists of a tuple of the form: ( reaction, quantity ).

    '''

    args = process_args()

    if args.stats or args.elemental_data_is_coupled:
        from x4i3 import exfor_manager, exfor_entry, exfor_reactions
        db = exfor_manager.X4DBManagerDefault()
        couplings = {}

    # Get the coupled data
    f = cPickle.load( open( args.inFile, mode='r' ) )
    
    # Get the monitor data
    m = cPickle.load( open( args.monFile, mode='r' ) )

    # Set up filters for what to put on graph
    targetFilterList = None
    projectileFilterList = None
    observableFilterList = None
    if args.filterFile != None:
        try:                import configparser
        except ImportError: import ConfigParser as configparser
        # Some other things we need to get from the configFile
        filterFile = configparser.ConfigParser()
        filterFile.read( args.filterFile )
#        print "DEBUG:",filterFile, args.filterFile
        try: projectileFilterList = eval( filterFile.get( 'filters', 'projectiles' ) )
        except: pass
        try: 
            targetFilterList = eval( filterFile.get( 'filters', 'targets' ) )
            if args.include_elem_to_iso: 
                targetFilterList = addElementsIsotopes( targetFilterList )
        except: pass
        try: observableFilterList = [ x.upper() for x in eval( filterFile.get( 'filters', 'observables' ) ) ]
        except: pass
    else:
        if args.neutron_only: projectileFilterList = [ 'n' ]
        if args.xsect_only: observableFilterList = [ 'SIG' ]
        
    # The filter functions
    def keepProjectile(x):
        if projectileFilterList == None: return True
        return x in projectileFilterList
    def keepTarget(x):
        if targetFilterList == None: return True
        return x in targetFilterList
    def keepObservable(x):
        if observableFilterList == None: return True
        return x in observableFilterList
        
    # Avoid code duplication later by pulling out the main node+connection decision logic
    def makeAConnectionWithNodes( entryKey, index, nodeFrom, nodeMap, monitor=True ):
        foundConnection = False
        rxnFrom = Reaction(nodeFrom[0])
        if not keepProjectile( str( rxnFrom.proj ) ): return
        if not keepTarget( str( rxnFrom.targ ) ): return
        if not keepObservable( nodeFrom[1] ): return
        for nodeTo in nodeMap[entryKey][i+1:]:
            rxnTo = Reaction(nodeTo[0])
            if not keepProjectile( str( rxnTo.proj ) ): return
            if not keepTarget( str( rxnTo.targ ) ): return  
            if not keepObservable( nodeTo[1] ): return  
            theGraph.addNodesAndLinks( \
                nodeFrom, nodeTo, \
                args.coupled_only, args.include_elem_to_iso, \
                args.elemental_data_is_coupled, args.verbose, monitor=monitor )
            foundConnection = True
        if foundConnection: 
            theReactionEquation = None
            if args.stats: 
                theEntryFile = db.retrieve( SUBENT=key[1] )
                theEntry = exfor_entry.X4Entry( theEntryFile[ key[0] ] )
                theReaction = theEntry[ key[1] ]['BIB'][ 'REACTION' ]
                if not len(nodeMap[entryKey]) in couplings: couplings[ len(nodeMap[entryKey]) ] = []
                theReactionEquation = theReaction.getEquation( entryKey[2] )
                couplings[ len(nodeMap[entryKey]) ].append( theReactionEquation )
                if args.verbose: 
                    print entryKey,':',nodeMap[entryKey],',', len(nodeMap[entryKey]),'items coupled via', ' '.join( theReaction.getEquation( entryKey[2] ) ) 
            allTheEXFORConnectedSets.append( EXFORConnectedSet( entryKey[0], entryKey[1], entryKey[2], theReactionEquation, nodeMap[entryKey] ) )


    # Set up the graph
    theGraph = Graph()
    keyList = unique( f.keys()+m.keys() )
    for key in keyList:   
        if args.verbose: 
            if key in m:    print key, '# MONITORS', len(m[key])
            else:           print key       
        if key in f:
            for i, nF in enumerate( f[key] ): makeAConnectionWithNodes( key, i, nF, f )
        if key in m:
            for i, nF in enumerate( m[key] ): makeAConnectionWithNodes( key, i, nF, m, monitor=True )
            
    if args.connectedSetsFile != None:
        open( args.connectedSetsFile, mode='w' ).writelines( [ '\t'.join( map( str, [ x.entry, x.subent, x.ptr, x.reactionEquation, x.reactions ] ) ) + '\n' for x in allTheEXFORConnectedSets ] )
        
    if args.stats: 
        theGraph.printStatistics()
        print "Degree of coupling statistics:"
        print '    # connections     # sets'
        for k in couplings:
            print '   ', k, 15*' ', len( couplings[k] )
        print
        for k in couplings:
            if k > 2: print "For",k,':', [ ' '.join( x ) for x in couplings[k] ]

    # Generate the node diagram in GraphML format
    if args.format == 'graphml':      
        # Layout file
        if args.verbose: print "Observable Types:", theGraph.clusterMap.keys()
        results = graphml_template.replace( \
                '#NODES', '\n'.join( [ '\n' + '\n'.join( [ decorateNode( x ) for x in theGraph.clusterMap[k] ] ) for k in theGraph.clusterMap ] ) \
            ).replace( \
                "#EDGES" , '\n'.join( [ decorateEdge( x.fr, x.to, edgeColor=x.color, numConnections = theGraph.connectionMap[x] ) for x in theGraph.connectionMap ] ) \
            ).replace( "#CLUSTERS" , '' )        
        # Save file, use external renderer
        open( args.outFilePrefix + '.' + args.format, mode='w' ).writelines( results )

    # Generate the node diagram using GraphViz in DOT format
    else:
        # Special formatting
        def specialStyle( x ): 
            if x in theGraph.specialNodeList: return '[ style="filled" color="gold" fillcolor="blue3" fontcolor="white" ]'
            return ''
        # Create file
        results = \
            dot_template.replace( \
                "#CONNECTIONS" , '\n'.join( [ '    "'+str(Node(x.fr)) +'" -- "' + str(Node(x.to)) + '" [color="black" weight=' + str( theGraph.connectionMap[x] * 1.00 + 1.00 ) + '];' for x in theGraph.connectionMap ] ) \
            ).replace( \
                '#CLUSTERS', '\n'.join( ['    subgraph cluster_'+k.replace('/','_')+'{\n        color="red";\n        packmode="clust";\n' + '\n'.join( \
                [ '        "'+str(Node(x))+'" '+specialStyle( x )+';' for x in theGraph.clusterMap[k] ] ) + '\n    }\n' for k in theGraph.clusterMap ] )\
            ).replace( \
                "#SPECIALNODESETTINGS", '\n'.join( [ '        "' + str(Node(y)) + '" [ style="filled" color="gold" fillcolor="blue3" fontcolor="white" ];' for y in theGraph.specialNodeList ] ) \
            )
        # Render the output
        if args.format == 'gv': open( args.outFilePrefix + '.' + args.format, mode='w' ).writelines( results )
        else: subprocess.Popen( [ args.renderer, '-Goverlap=prism', '-T'+args.format, '-o'+args.outFilePrefix+'.'+args.format ], stdin = subprocess.PIPE ).communicate( input = results )
        '''sfdp -Goverlap=prism coupled_EXFOR_data_visualization.gv | gvmap -e -a 20 | neato -Ecolor="#55555522" -n2 -Tpdf > coupled_EXFOR_data_visualization.pdf'''

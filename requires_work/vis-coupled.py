#! /usr/bin/env python
'''
vis-coupled.py

Authors: J Hirdt, D.A. Brown

'''
from x4i3 import __path__, abundance, endl_Z,fullMonitoredFileName, fullCoupledFileName, fullReactionCountFileName
import sys, os, argparse
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
    parser.add_argument("-r", default=fullReactionCountFileName, dest="recFile", type=str, help = "Full Reaction Data pickle file containing information on all reactions in EXFOR [default: "+fullReactionCountFileName+"]")
    parser.add_argument("--max_count", default=None, type=int, help="Max number of nodes to process in a graph [Default: 'None']" ) 
    parser.add_argument("--get_node_info", default = None, type = str, help = "Get the info for a specific node[Default: 'None']" ) 
    parser.add_argument('--make_graph', default=False, action='store_true', help="Turn true to make the visualization appear" )
    parser.add_argument('--ddf', default=False, action = 'store_true', help="Turn on True to make degree distribution function histogram appear")
    parser.add_argument('--show_clustering_distribution', default=False, action = 'store_true', help="Turn on True to make clustering distribution function histogram appear")
    parser.add_argument('--get_distances_to_standard', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to standard reactions ")
    parser.add_argument('--get_distances_to_proposed_standard', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to proposed standard reactions ")
    parser.add_argument('--get_distances_to_proposed_and_standard', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to proposed and standard reactions ")
    parser.add_argument('--get_distances_to_special_nodes', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to special nodes ")
    parser.add_argument('--get_distances_to_special_or_proposed_nodes', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to proposed and special nodes" )
    parser.add_argument('--get_distances_to_dosimiter_or_proposed_nodes', default = False, action = 'store_true', help = "Turn on true to get the distances and the histogram for the distribution of distances to dosimiter and proposed nodes" )
    parser.add_argument('--get_cumulative_histogram', default = False, action='store_true', help= "Get a cumulative histogram ontop of one another")
    parser.add_argument('--get_distances_to_CIELO', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to CIELO reactions ")
    parser.add_argument('--get_distances_to_dosimiter', default = False, action='store_true', help= "Turn on true to get the distances and the historgram for the distribution of distances to dosimiter reactions ")
    parser.add_argument('--get_independent_cluster_info', default = False, action='store_true', help= "Turn on true to get the independent clusters from standard, CIELO or Dosimiter ")
    parser.add_argument('--show-reaction',              dest= 'showReaction',   default = True,     action='store_true',        help = "Show all reactions")
    parser.add_argument('--no-show-reaction',           dest= 'showReaction',   default = True,     action='store_false',       help = "Do not show all reactions, show only those explicitly requested with other switches")
    parser.add_argument('--show-coupled',               dest='showCoupled',     default=True,       action='store_true',        help="Show coupled reaction data" )
    parser.add_argument('--no-show-coupled',            dest='showCoupled',     default=True,       action='store_false',       help="Do not show coupled reaction data" )
    parser.add_argument('--show-standards',             dest='showStandard',    default =True,      action = 'store_true',      help="Show neutron standard reactions")
    parser.add_argument('--no-show-standards',          dest='showStandard',    default =True,      action = 'store_false',     help="Do not show neutron standard reactions")
    parser.add_argument('--show-cielo',                 dest = 'showCielo',     default = True,     action = 'store_true',      help = "Show CIELO isotopes")
    parser.add_argument('--no-show-cielo',              dest = 'showCielo',     default = True,     action = 'store_false',     help = "Do not show CIELO isotopes")
    parser.add_argument('--show-dosimiter',                 dest = 'showDosimiter',     default = True,     action = 'store_true',      help = "Show Dosimiter reactions")
    parser.add_argument('--no-show-dosimiter',              dest = 'showDosimiter',     default = True,     action = 'store_false',     help = "Do not show Dosimiter reactions")
    parser.add_argument('--show-almost-standards',      dest = 'showAlmostStandard', default = True, action = 'store_true',     help = "Show the reactions that were evaluated at the same time as the neutron standards")
    parser.add_argument('--no-show-almost-standards',   dest = 'showAlmostStandard', default = True, action = 'store_false',    help = "Do not the reactions that were evaluated at the same time as the neutron standards")
    parser.add_argument('--show-monitor',               dest='showMonitor',     default=True,       action='store_true',        help="Show monitor reaction data" )
    parser.add_argument('--no-show-monitor',            dest='showMonitor',     default=True,       action='store_false',       help="Do not show monitor reaction data" )
    parser.add_argument('--show-elemental',             dest='showElemental',   default=True,       action='store_true',        help="Show elemental reaction data" )
    parser.add_argument('--no-show-elemental',          dest='showElemental',   default=True,       action='store_false',       help="Do not show elemental reaction data" )
    parser.add_argument('--show-same-target-links',     dest='showTargLink',   default=False,       action='store_true',         help="Show edges between all reactions on the same target" )
    parser.add_argument('--no-same-target-links',       dest='showTargLink',   default=False,       action='store_false',        help="Do not show edges between all reactions on the same target" )
    parser.add_argument('--show-same-target-projectile-links',  dest='showTargProjLink',    default=False,   action='store_true',    help="Show edges between all reactions with the same target and projectile" )
    parser.add_argument('--no-same-target-projectile-links',    dest='showTargProjLink',    default=False,   action='store_false',   help="Do not show edges between all reactions with the same target and projectile" )
    parser.add_argument('--get_nodes_with_degree', default=None, dest='degreeForNodes', type=int, help="Get the list of nodes with the degree specified here.  Use -10 for the degree of disconnected nodes." ) 
    parser.add_argument('--get_degree_for_node', default=None, dest='nodeForDegree', type=str, help="Get the degree of a node specified here.  Use -10 for the degree of disconnected nodes." )
    parser.add_argument('--get_degree_list', dest='degreelist', default = False, action= 'store_true', help = "Show a numerical list of all the unique degrees a node may have in the graph" )
    parser.add_argument('--show-special-quants',dest='showSpecialQuants', default=True, action='store_true', help="Show special quantity data" )
    parser.add_argument('--no-show-special-quants',dest='showSpecialQuants', default=True, action='store_false', help="Do not show special quantity data" )
    parser.add_argument('--show-inclusive-process', dest='showInclusiveProcess', default=True, action='store_true', help="Show inclusive process data" )
    parser.add_argument('--no-show-inclusive-process', dest='showInclusiveProcess', default=True, action='store_false', help="Do not show inclusive process data" )
    parser.add_argument('--cluster', default = False, action='store_true', help= "Turn on True to get clustering coefficients for nodes in the graph")
    parser.add_argument("--get_neighbors", default=None, type=str, help="Enter a node to print out a list of neighbors [Default: 'None']" ) 
    parser.add_argument('--spectral_density', default=False, action = 'store_true', help="Turn on True to make spectral density histogram appear")
    parser.add_argument('--show-cross-section-only',    dest='showCrossOnly',       default = False,    action='store_true',        help="Show only cross-section data and nothing else")
    parser.add_argument('--show-neutron-only',      dest='showNeutronOnly',     default = False,    action = 'store_true',      help = "Show only neutron reactions and nothing else")
    parser.add_argument('--show-proton-only',           dest='showProtonOnly',      default = False,    action = 'store_true',      help = "Show only proton reactions and nothing else")
    parser.add_argument('--show-deuteron-only',     dest='showDeuteronOnly',   default = False,       action='store_true',         help="Show deuteron rxn only" )
    parser.add_argument('--no-show-deuteron-only',  dest='showDeuteronOnly',   default=False,       action='store_false',        help="Do not show Show deuteron rxn only" )
    parser.add_argument('--show-HE3-only',     dest='showHE3Only',   default=False,       action='store_true',         help="Show HE3 reactions only" )
    parser.add_argument('--no-show-HE3-only',       dest='showHE3Only',   default=False,       action='store_false',        help="Do not show Show HE3 reactions only" )
    parser.add_argument('--show-alpha-only',     dest='showAlphaOnly',   default=False,       action='store_true',         help="Show alpha ractions only" )
    parser.add_argument('--no-show-alpha-only',       dest='showAlphaOnly',   default=False,       action='store_false',        help="Do not show alpha reactions only" )
    parser.add_argument('--show-gamma-only',     dest='showGammaOnly',   default=False, action='store_true',         help="show gamma reactions only" )
    parser.add_argument('--no-show-gamma-only',  dest='showGammaOnly',   default=False, action='store_true',         help="Do not show gamma reactions only" )
    parser.add_argument('--show-carbon-only',     dest='showCarbonOnly',   default=False, action='store_true',         help="show carbon reactions only" )
    parser.add_argument('--no-show-carbon-only',  dest='showCarbonOnly',   default=False, action='store_true',         help="Do not show carbon reactions only" )
    parser.add_argument('--show-triton-only',     dest='showTritonOnly',   default=False, action='store_true',         help="show tritium reactions only" )
    parser.add_argument('--no-show-triton-only',  dest='showTritonOnly',   default=False, action='store_true',         help="Do not show tritium reactions only" )   
    parser.add_argument( '--subgraph-number', dest='subGraphNumber', default=None, type=int, help="Chop the graph into disconnected subgraphs, rank order them and take this one for subsequent processing [only for plotting currently, and default is to show entire graph]" ) 
    parser.add_argument("--format", default='graphml', dest='format', type=str, choices = [ 'graphml' ], help="Output format for graph [Default: 'graphml']" ) 
    parser.add_argument("--outFile_prefix", type=str, dest='outFilePrefix', default=None, help="the prefix of the output files")
    parser.add_argument('--get_info', default= False, action = 'store_true', help = "Turn on to get info about the graph" )
    parser.add_argument('--get_top_20_info', default=False, action ='store_true', help = "Turn on to get info about the top 20 most connected things in the graph" )
    parser.add_argument('--eccentricity_distribution', default = False, action = 'store_true', help = "Turn on to get the eccentricity histogram, Note: this will only work for a connected graph" )
    parser.add_argument('--get_subgraph_plots', default = False, action = 'store_true', help = "Get all the subgraphs with count of nodes higher than 10" )
    parser.add_argument('--get_unconnected_cluster_info', default = False, action = 'store_true', help = "Get unconnected cluster info/plots" )
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
    import x4i.vis_graph
    args = process_args()
    G = x4i.vis_graph.graph_init()
    monitored_edges         = []
    coupled_edges           = []
    cielo_edges             = []
    almost_standard_edges   = []
    standard_edges          = []
    element_edges           = []
    target_edges            = []
    target_proj_link_edges  = []
    inclusive_process_edges = []    
    special_quants_edges    = []

    # ---- Graph addition operations -----
    
    if args.showStandard and args.showAlmostStandard:standard, almost_standard_edges = x4i.vis_graph.add_standard_almost_standard(args.max_count, G, standard_edges, almost_standard_edges)    

    else:
        if args.showStandard: x4i.vis_graph.standard_edges = add_standards(args.max_count, G, standard_edges)
    
        if args.showAlmostStandard:x4i.vis_graph.almost_standard_edges = add_almost_standards(args.max_count, G, almost_standard_edges)
          
    #Need to figure out nodeInstance first  
    #if args.showCielo:cielo_edges = x4i.vis_graph.add_CIELO(G, cielo_edges )  
                     
    if args.showCoupled: coupled_edges = x4i.vis_graph.add_Coupled(args.max_count, args.inFile, G, coupled_edges )
        
    if args.showMonitor: monitored_edges = x4i.vis_graph.add_Monitor(args.max_count, args.monFile, args.verbose, G, monitored_edges ) 
        
    if args.showReaction:x4i.vis_graph.add_Reaction(args.max_count, args.recFile, G)
        
    if args.showElemental:element_edges=x4i.vis_graph.add_elemental(args.max_count, G, element_edges )
        
    if args.showInclusiveProcess:inclusive_process_edges = x4i.vis_graph.add_inclusive(args.max_count, G, inclusive_process_edges)
                
    if args.showSpecialQuants:special_quants_edges = x4i.vis_graph.add_special_quants(args.max_count, G, special_quants_edges)    
 
    if ( args.showInclusiveProcess or args.showSpecialQuants ) and  args.showElemental: element_edges = x4i.vis_graph.add_special_elemental(args.max_count, G, element_edges)
        
    # ---- Filtering graph operations -----
    
    if args.showCrossOnly:x4i.vis_graph.keep_only_cross(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)   
        
    if args.showNeutronOnly:x4i.vis_graph.keep_only_neutron(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showProtonOnly:x4i.vis_graph.keep_only_proton(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showDeuteronOnly:x4i.vis_graph.keep_only_deuteron(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showAlphaOnly:x4i.vis_graph.keep_only_alpha(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showGammaOnly:x4i.vis_graph.keep_only_gamma(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showHE3Only:x4i.vis_graph.keep_only_HE3(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showTritonOnly:x4i.vis_graph.keep_only_triton(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showCarbonOnly:x4i.vis_graph.keep_only_carbon(G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)
        
    if args.showTargLink:target_edges = x4i.vis_graph.keep_only_target(G, target_edges)
        
    if args.showTargProjLink:target_proj_link_edges = x4i.vis_graph.keep_only_target_proj(G, target_proj_link_edges)
        
    # ---- Analysis operations -----    
    
    if args.make_graph:                                         x4i.vis_graph.generate_graph(args.outFilePrefix, G, standard_edges, almost_standard_edges, cielo_edges, coupled_edges, monitored_edges, element_edges, inclusive_process_edges, special_quants_edges, target_edges, target_proj_link_edges)

    if args.ddf:                                                x4i.vis_graph.get_ddf(args.outFilePrefix, G)

    if args.degreelist or args.get_top_20_info:                 top20list = x4i.vis_graph.get_degree_tuple(G)

    if args.degreeForNodes!=None or args.nodeForDegree!=None:   x4i.vis_graph.get_node_degree_info()

    if args.get_distances_to_dosimiter:                         x4i.vis_graph.get_distance_D(args.outFilePrefix, G)

    if args.get_distances_to_special_nodes:                     x4i.vis_graph.get_distance_special(args.outFilePrefix, G)

    if args.get_distances_to_dosimiter_or_proposed_nodes:       x4i.vis_graph.get_distance_D_P(args.outFilePrefix, G)

    if args.get_distances_to_special_or_proposed_nodes:         x4i.vis_graph.get_distance_special_P(args.outFilePrefix, G)

    if args.get_distances_to_CIELO:                             x4i.vis_graph.get_distance_C(args.outFilePrefix, G)

    if args.get_distances_to_standard:                          x4i.vis_graph.get_distance_S(args.outFilePrefix, G)

    if args.get_distances_to_proposed_standard:                 x4i.vis_graph.get_distance_P(args.outFilePrefix, G)

    if args.get_distances_to_proposed_and_standard:             x4i.vis_graph.get_distance_P_S(args.outFilePrefix, G)

    if args.get_cumulative_histogram:                           x4i.vis_graph.get_cumulative_histogram(args.outFilePrefix, G)

    if args.get_independent_cluster_info:                       x4i.vis_graph.get_independent_cluster(args.outFilePrefix, G)

    if args.get_unconnected_cluster_info:                       x4i.vis_graph.get_unconnected_cluster(args.outFilePrefix, G)
                
    if args.cluster:                                            x4i.vis_graph.get_cluster(G)

    if args.show_clustering_distribution:                       x4i.vis_graph.get_clustering_distribution(args.outFilePrefix, G)

    if args.get_neighbors:                                      x4i.vis_graph.get_neighbor()
        
    if args.spectral_density:                                   x4i.vis_graph.get_spectral_density(args.outFilePrefix, G)
        
    if args.get_info:                                           x4i.vis_graph.get_graph_info(args.get_node_info, G)

    if args.get_top_20_info:                                    x4i.vis_graph.get_top20info(args.outFilePrefix, G, top20list)

    if args.eccentricity_distribution:                          x4i.vis_graph.get_eccentricity(G)

    if args.get_subgraph_plots:                                 x4i.vis_graph.get_subgraphs(args.outFilePrefix, G)         

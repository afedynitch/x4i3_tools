#! /usr/bin/env python
'''
function_test_graph.py

Authors: J Hirdt, D.A. Brown

'''

import networkx as nx
import matplotlib.pyplot as plt
import argparse
import cPickle
from networkx.generators.degree_seq import *
import cPickle
import time
import scipy
# -----------------------------------------------------------------------
#    Command line parsing
# -----------------------------------------------------------------------


def process_args():
    parser = argparse.ArgumentParser(
        description='Visualize coupled datasets in the EXFOR library using GraphViz')
    parser.set_defaults(verbose=False)
    parser.add_argument(
        '--testfunction1',
        dest='function1',
        default=False,
        action='store_true',
        help="Show reaction data")
    parser.add_argument(
        '--testfunction2',
        dest='function2',
        default=False,
        action='store_true',
        help="Show graph tool reaction data")
    parser.add_argument(
        '--reaction-count',
        dest='rxncount',
        default=False,
        action='store_true',
        help="Show rxncount testing")
    parser.add_argument(
        '--test_time',
        dest='timetest',
        default=False,
        action='store_true',
        help="Show datetime testing")
    return parser.parse_args()
# -----------------------------------------------------------------------
#   Class Function Test
# -----------------------------------------------------------------------


class Function_Test:

    # Trial and Error code to figure out use and capabilities of networkx functions

    def __init__(self, node0, node1, graph=None, count=0):
        self.node0 = node0
        self.node1 = node1
        self.graph = graph
        self.count = count


# -----------------------------------------------------------------------
#    Main routine
# -----------------------------------------------------------------------

if __name__ == "__main__":
    args = process_args()
    G = nx.Graph()
    if args.function2:

        from graph_tool.all import *
        #import graph_tool as gt
        g = Graph(directed=False)
        name11 = g.new_vertex_property("string")
        node_color = g.new_vertex_property('string')
        node_fill_color = g.new_vertex_property('string')

        a = g.add_vertex()
        '''
        name11[g.vertex(a)] = 'natCU'
        name11[g.vertex(b)] = '65CU'
        name11[g.vertex(c)] = '63CU'
        edge = g.add_edge(a,b)
        dege = g.add_edge(b,c)
        gedg = g.add_edge(a,c)
        '''
        graph_draw(
            g,
            vertex_color='#000000',
            vertex_fill_color='#ffffff',
            edge_color='#0cf232')

    if args.function1:
        '''
        #Small Node Test
        cccc = time.clock( )
        G.add_node('B-0(N,SCT)SIG')
        G.add_node('B-0(N,INL)SIG')
        G.add_node('B-0(N,EL)SIG')
        #G.add_node('U-235(N,F)ETA')
        G.add_edges_from([('B-0(N,SCT)SIG','B-0(N,INL)SIG'),('B-0(N,SCT)SIG','B-0(N,EL)SIG'),('B-0(N,INL)SIG','B-0(N,EL)SIG')])#,('U-235(N,F)SIG','U-235(N,F)NU'),('U-235(N,F)SIG','U-235(N,G)SIG')])

        G.add_node("'U-0(N,EL)', 'DA'")
        G.add_node("'U-0(N,INL)', 'DA'")
        G.add_edge("'U-0(N,EL)', 'DA'","'U-0(N,INL)', 'DA'")
        G.add_node("'BI-209(N,X+2-HE-4)', 'DA/DE'")
        G.add_node("'BI-209(N,X+2-HE-3)', 'DA/DE'")
        G.add_edge("'BI-209(N,X+2-HE-4)', 'DA/DE'","'BI-209(N,X+2-HE-3)', 'DA/DE'")
        G.add_node("'U-234(N,F)', 'SIG'")
        G.add_node("'U-235(N,F)', 'SIG'")
        G.add_edge("'U-234(N,F)', 'SIG'","'U-235(N,F)', 'SIG'")
        G.add_node("'NI-58(N,EL)', 'WID'")
        G.add_node("'NI-58(N,G)', 'WID'")
        G.add_node("'NI-58(N,TOT)', 'WID'")
        G.add_edge("'NI-58(N,EL)', 'WID'","'NI-58(N,TOT)', 'WID'")
        G.add_edge("'NI-58(N,TOT)', 'WID'" , "'NI-58(N,G)', 'WID'")
        G.add_edge("'NI-58(N,G)', 'WID'", "'NI-58(N,EL)', 'WID'")
        G.add_edge("'NI-58(N,G)', 'WID'","'BI-209(N,X+2-HE-4)'")
        G.add_edge("'LI-7(D,A)', 'SIG'","'NI-58(N,G)', 'WID'")
        G.add_node("'LI-7(D,A)', 'SIG'")
        #print nx.eigenvalue_centrality( G )
        '''
        '''
        G.add_node(1)
        G.add_node(2)
        G.add_node(3)
        G.add_node(4)
        G.add_node(5)
        G.add_node(6)
        G.add_edge(1,2)
        G.add_edge(1,3)
        G.add_edge(2,3)
        G.add_edge(2,4)
        G.add_edge(2,5)
        G.add_edge(3,4)
        G.add_edge(4,5)
        G.add_edge(5,6)
        '''
        G.add_node(1)
        G.add_node(2)
        G.add_node(3)
        G.add_edge(1, 2)
        G.add_edge(2, 3)
        G.add_edge(3, 1)

        G.add_node(4)
        G.add_node(5)
        G.add_node(6)
        G.add_edge(4, 5)
        G.add_edge(5, 6)
        G.add_edge(4, 6)

        # nx.draw(G)
        # plt.show()
        #plt.savefig('savingtest.png', bbox_inches = 0)
        # print nx.eigenvector_centrality( G )

        k = [1, 1, 1, 1, 1, 2, 2, 2, 3, 3, 3, 5, 5, 5, 7, 7, 7, 8, 9, 10]
        import matplotlib.pyplot as plt
        '''
        from pylab import hist35
        hist(k, bins = 11)
        plt.title('test')        degree = [10, 10,10,10,25,25,25,32,32,40,40
        plt.xlabel('freq')
        plt.axis([-.5,10.5,0,10])
        plt.show()
        plt.clf()
        '''
        '''
        degree = [10, 10,10,10,25,25,25,32,32,40,40,36,35,40,35,50,46,25,32,45]
        tupleList = []
        degree = sorted(degree)
        for k in degree:
            count = 0
            for p in degree:
                if k == p:count = count + 1
                else: pass
            p = (k,count)
            if p not in tupleList:tupleList.append(p)
            else: pass
        left = []
        height = []
        for x in tupleList:
            left.append(x[0]-.5)
            height.append(x[-1])
        print left
        print height

        plt.bar(left, height, width = 1)
        plt.show()
        '''

        randList = [(8, 9), (4, 6), (3, 5), (9, 1), (3, 5)]

    # -----------------------------------------------------------------------
    #   Density Function Tests
    # -----------------------------------------------------------------------

        # Test Density Function

        def get_graph_density(graph):
            dense = nx.density(graph)
            return dense

    # -----------------------------------------------------------------------
    #   Degree Histogram Function Tests
    # -----------------------------------------------------------------------
        print "Start", time.clock()
        # Test Degree Histogram Function
        histogram_list = nx.degree_histogram(G)
        plt.loglog(histogram_list, 'b-', marker='o')
        plt.ylabel("Degree")
        plt.xlabel("Nodes")
        # Command to actually plot graph
        # plt.show()
        print "End", time.clock()

    # -----------------------------------------------------------------------
    #   Degree Histogram Function Tests
    # -----------------------------------------------------------------------

        # Test Degree Function
        def get_node_degree(graph, node0):
            dgre = nx.degree(graph, node0)
            return dgre

    # -----------------------------------------------------------------------
    #   Shortest Path Function Tests
    # -----------------------------------------------------------------------

        # Test all_shortest_path function

        def get_path_between_nodes(graph, node0, node1):
            path = ([p for p in nx.all_shortest_paths(graph, source=node0, target=node1)])
            return path

    # -----------------------------------------------------------------------
    #   Shortest Path Length Function Tests
    # -----------------------------------------------------------------------

        # Test the distance from one node to another node
        def get_distance_between_nodes(graph, node0, node1):
            distance = nx.shortest_path_length(graph, source=node0, target=node1)
            return distance

    # -----------------------------------------------------------------------
    #   Unit Tests
    # -----------------------------------------------------------------------
        '''
        import unittest
        class Test_Function_Test( unittest.TestCase ):
        def test_get_distance_between_nodes( self ):
            self.assertTrue(
        '''
    # -----------------------------------------------------------------------
    #   Function Tests
    # -----------------------------------------------------------------------

        # print get_distance_between_nodes(G, 1, "test")
        print "Start", time.clock()
        for k in G.nodes():
            neighbor_list = []
            for p in G.nodes():
                try:
                    distance = get_distance_between_nodes(G, k, p)
                    if distance == 1:
                        if p not in neighbor_list:
                            neighbor_list.append(p)
                except nx.NetworkXNoPath:
                    pass
                except nx.NetworkXError:
                    pass
        print "End", time.clock()
        # print k, neighbor_list
    # -----------------------------------------------------------------------
    #   Function Tests
    # -----------------------------------------------------------------------
    if args.rxncount:
        print cluster_list

    '''
        sdd = time.clock( )
        eigenList = []
        e=nx.eigenvector_centrality(G)
        e = e.values()
        el = sorted(e)
        for k in el:
            eigenList.append(k)
        x = []
        y = []
        for r in eigenList:
            x.append(r)
            z = ((math.sqrt(4.0*87590*(.0000439)*(1-.0000439)-(math.pow(r, 2))))/(2*math.pi*87590*(.0000439)*(1-.0000439)))
            y.append(z)
        plt.plot(x,y,marker='o')
        plt.title("Spectral Density")
        plt.ylabel("p")
        plt.xlabel("lambda")
        plt.show()
        nsd = time.clock( )
        print "Spectral Density Takes", nsd-sdd, "Seconds"
        '''

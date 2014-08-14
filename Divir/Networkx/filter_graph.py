import  networkx as nx
import matplotlib.pyplot as plt
import time

def filter_price_change(G, threshold):
    unsignificant_nodes = []
    for name in G:
        if G.node[name]['type'] == 'Company' and G.node[name]['price_change'] >= threshold:
            G.node[name]['label'] += ' : ' + str(G.node[name]['price_change'])
            print G.node[name]['label'], True
            continue

        neighbors = G.neighbors(name)
        significant = False

        for neighbor in neighbors:
            if G.node[neighbor]['type'] == 'Company' and G.node[neighbor]['price_change'] >= threshold:
                significant = True
                break

        print G.node[name]['label'], significant

        if not significant: unsignificant_nodes.append(name)
        if significant and G.node[name]['type'] == 'Company':
            G.node[name]['label'] += ' : ' + str(G.node[name]['price_change'])

    G.remove_nodes_from(unsignificant_nodes)
    return G

def drawGraph(G):
    pos = nx.spring_layout(G)
    nx.draw_networkx_nodes(G,pos)
    nx.draw_networkx_labels(G,pos, font_size=5)

    plt.axis('off')
    plt.savefig('../Data/Price-Heat-Graphs/' + date + '-filtered.png', dpi=1000)


def filter_nodes_by_occurence(G, low, high):
    # remove nodes if less than low and more than high
    print "\nBefore filtering by occurence low: %d, high: %d, nodes: %d, edges: %d" % \
          (low, high, nx.number_of_nodes(G), nx.number_of_edges(G))

    [ G.remove_node(node) for node in G.nodes() if not low <= G.node[node]['size'] <= high ]

    print "After filtering by occurence low: %d, high: %d, nodes: %d, edges: %d\n" % \
          (low, high, nx.number_of_nodes(G), nx.number_of_edges(G))
    return G

def filter_edges_by_weight(G, low, high):
    # remove edges if less than low and more than high
    print "\nBefore filtering by edge weight low: %d, high: %d, nodes: %d, edges: %d" % \
          (low, high, nx.number_of_nodes(G), nx.number_of_edges(G))

    # remove edges
    [ G.remove_edge(source, target) for source, target in G.edges() if not low <= G[source][target]['weight'] <= high ]

    # remove nodes with no edges
    [ G.remove_node(node) for node in G.nodes() if nx.degree(G, node) == 0 ]

    print "After filtering by edge weight low: %d, high: %d, nodes: %d, edges: %d\n" % \
          (low, high, nx.number_of_nodes(G), nx.number_of_edges(G))
    return G

def log_time(fun, *args):
    # print time taken by function
    start_time = time.time()
    result = fun(*args)
    elapsed_time = time.time() - start_time
    print "%s , time taken: %.2f" % (fun.__name__, elapsed_time)
    return result


date = '2014-07-01'
path = '../Data/Price-Heat-Graphs/'

G = nx.read_gexf(path + date + '.gexf')
#G = log_time(filter_nodes_by_occurence, G, 5, 200)
G = log_time(filter_edges_by_weight, G, 0.001, 1)

# nx.write_gexf(G, path + date + '-filtered.gexf')



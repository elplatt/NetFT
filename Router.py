
# coding: utf-8

# In[ ]:

import math
import os
import random
import re
import sys
import time
from multiprocessing import Process, Queue
import networkx as nx
from networkx.algorithms.components import connected_components
from networkx.algorithms.connectivity import node_connectivity
from networkx.algorithms.centrality.betweenness import betweenness_centrality
from networkx.algorithms.distance_measures import diameter
import numpy as np
import elp_networks as elpnet
import elp_networks.algorithms as elpalg
import logbook


# In[ ]:

rewire_f = 0.9
#rewire_f = sys.argv[1]
butterfly_m = 7
num_conn_pairs = 150
net_file = "external/as20000102.csv"
out_file = "stats.csv"
try:
    job_id = os.environ["PBS_ARRAYID"]
except KeyError:
    job_id = 0
exp_name = "router_targeted"
exp_suffix = str(job_id)
exp_ts = str(time.time())


# In[ ]:

random.seed(hash('''
    Build a man a fire, and he'll be warm for a day.
    Set a man on fire, and he'll be warm for the rest of his life.
                                                –Terry Pratchett
''' + exp_ts + str(job_id)))


# In[ ]:

def rewire_butterfly(g, fraction, butterfly_m):
    m = butterfly_m
    # Create butterfly and shuffle edges
    butterfly = elpnet.Butterfly(m)
    bf_nodes = list(butterfly.int_nodes())
    bf_edges = set()
    for bv in bf_nodes:
        for bw in butterfly.int_neighbors(bv):
            bf_edges.add(tuple(sorted([bv,bw])))
    bf_edges = list(bf_edges)
    random.shuffle(bf_edges)
    num_bnodes = len(bf_nodes)
    # Only sample nodes that can be completely rewired
    # This list maps butterfly node labels to router node labels
    rewire_nodes = random.sample([n for n in g.nodes() if len(list(g.neighbors(n))) >= 4], num_bnodes)
    router_to_bf = dict([(r, b) for b, r in enumerate(rewire_nodes)])
    router_edges = set()
    for rv in rewire_nodes:
        for rw in g.neighbors(rv):
            if rw in rewire_nodes:
                router_edges.add(tuple(sorted([rv, rw])))
    router_edges = list(router_edges)
    random.shuffle(router_edges)
    to_rewire = int(math.floor(fraction * len(bf_edges)))
    for i in range(to_rewire):
        rv, rw = router_edges.pop()
        g.remove_edge(rv, rw)
        bv, bw = bf_edges.pop()
        rv = rewire_nodes[bv]
        rw = rewire_nodes[bw]
        g.add_edge(rv, rw)


# In[ ]:

edge_list = []
whitespace = re.compile(r"\w+")
nodes = set()
with open(net_file, "rb") as f:
    for row in f:
        if row.startswith("#"):
            continue
        source, target = re.split(r"\W+", row.strip())
        source = int(source.strip())
        target = int(target.strip())
        nodes.add(source)
        nodes.add(target)
        edge_list.append( (source,target) )
node_count = len(nodes)


# In[ ]:

def do_failure_work(g):
    centralities = betweenness_centrality(g, normalized=False)
    v, c = max(centralities.iteritems(), key=lambda x: x[1])
    return v, c

def failure_worker(graph_q, component_inq, connectivity0_inq, connectivity1_inq, connectivity2_inq, connectivity3_inq, failure_outq):
    while True:
        g = graph_q.get()
        component_inq.put(g)
        connectivity0_inq.put(g)
        connectivity1_inq.put(g)
        connectivity2_inq.put(g)
        connectivity3_inq.put(g)
        v, c = do_failure_work(g)
        failure_outq.put((v,c))
        if c > 0:
            next_g = g.copy()
            next_g.remove_node(v)
            graph_q.put(next_g)


# In[ ]:

def do_component_work(g):
    return list(connected_components(g))

def component_worker(component_inq, diameter_inq, size_inq):
    while True:
        g = component_inq.get()
        components = do_component_work(g)
        diameter_inq.put( (components, g) )
        size_inq.put(components)


# In[ ]:

def do_diameter_work(components, g):
    giant_nodes = set(max(components, key=len))
    giant_edges = []
    for source, target in g.edges():
        if source in giant_nodes and target in giant_nodes:
            giant_edges.append( (source, target) )
    giant = nx.Graph(giant_edges)
    return diameter(giant)

def diameter_worker(diameter_inq, diameter_outq):
    while True:
        components, g = diameter_inq.get()
        diameter = do_diameter_work(components, g)
        diameter_outq.put(diameter)


# In[ ]:

def do_size_work(components):
    giant_nodes = max(components, key=len)
    total = sum([len(x) for x in components])
    try:
        result = float(total - len(giant_nodes)) / float(len(components) - 1)
    except ZeroDivisionError:
        result = 0
    return result

def size_worker(size_inq, size_outq):
    while True:
        components = size_inq.get()
        size_outq.put(do_size_work(components))


# In[ ]:

def sample_pairs(nodes, num):
    # Sample sources and targets
    sources = random.sample(nodes, num)
    targets = random.sample(nodes, num)
    # Replace self loops
    for i in range(num - 1):
        if sources[i] == targets[i]:
            sources[i], sources[-1] = sources[-1], sources[i]
    if sources[-1] == targets[-1]:
        sources[-1] = random.choice(set(nodes) - set(sources))
    return zip(sources, targets)
    
def expand(g, source, radius):
    if radius == 0:
        return set(), set()
    # Get all nodes within radius
    neighbors = set(nx.ego_graph(g, source, radius=radius).nodes())
    neighbors.remove(source)
    # Keep track of the boundary and remove nodes within radius
    boundary = set()
    for v in neighbors:
        boundary |= set(nx.neighbors(g, v))
    # Remove source (unless boundary is empty)
    boundary.discard(source)
    return neighbors, boundary
        
def do_connectivity_work(g, radius):
    pairs = sample_pairs(g.nodes(), num_conn_pairs)
    # Calculate connectivity for sampled pairs
    connectivities = []
    for source, target in pairs:
        s_neighbors, s_boundary = expand(g, source, radius)
        t_neighbors, t_boundary = expand(g, target, radius)
        expanded = g.copy()
        # Get list of all neighbors, remaining s/t boundaries
        neighbors = (t_neighbors | s_neighbors) - set([target]) - set([source])
        s_boundary -= neighbors
        t_boundary -= neighbors
        # If neighborhoods overlap, combine
        common = s_neighbors & t_neighbors
        if len(common) > 0:
            boundary = (s_boundary | t_boundary) - set([target]) - set([source])
            s_boundary = boundary
            t_boundary = boundary
            target = source
        # Remove neighbors and create edges to boundary
        for v in s_boundary:
            expanded.add_edge(source, v)
        for v in t_boundary:
            expanded.add_edge(target, v)
        for v in neighbors:
            expanded.remove_node(v)
        try:
            c = node_connectivity(expanded, source, target)
        except nx.NetworkXError:
            print source, target
            print s_boundary
            print t_boundary
            print neighbors
            raise
        connectivities.append(c)
    # Calculate statistics
    mean = np.mean(connectivities)
    std = np.std(connectivities, ddof=1)
    se = mean / np.sqrt(len(connectivities))
    return (mean, se)

def connectivity_worker(connectivity_inq, connectivity_outq, radius):
    while True:
        g = connectivity_inq.get()
        data = do_connectivity_work(g, radius)
        connectivity_outq.put(data)


# In[ ]:

graph_q = Queue(maxsize=4)
failure_outq = Queue()
component_inq = Queue(maxsize=4)
diameter_inq = Queue(maxsize=4)
diameter_outq = Queue()
size_inq = Queue(maxsize=4)
size_outq = Queue()
connectivity0_inq = Queue(maxsize=4)
connectivity0_outq = Queue()
connectivity1_inq = Queue(maxsize=4)
connectivity1_outq = Queue()
connectivity2_inq = Queue(maxsize=4)
connectivity2_outq = Queue()
connectivity3_inq = Queue(maxsize=4)
connectivity3_outq = Queue()

exp = logbook.Experiment(exp_name, suffix=exp_suffix)
log = exp.get_logger()

log.info("Rewiring graph")
g = nx.Graph(edge_list)
rewire_butterfly(g, rewire_f, butterfly_m)
graph_q.put(g)

log.info("Starting workers")
workers = []
workers.append(Process(target=failure_worker, args=(graph_q, component_inq, connectivity0_inq, connectivity1_inq, connectivity2_inq, connectivity3_inq, failure_outq)))
workers.append(Process(target=component_worker, args=(component_inq, diameter_inq, size_inq)))
workers.append(Process(target=diameter_worker, args=(diameter_inq, diameter_outq)))
workers.append(Process(target=size_worker, args=(size_inq, size_outq)))
workers.append(Process(target=connectivity_worker, args=(connectivity0_inq, connectivity0_outq, 0)))
workers.append(Process(target=connectivity_worker, args=(connectivity1_inq, connectivity1_outq, 1)))
workers.append(Process(target=connectivity_worker, args=(connectivity2_inq, connectivity2_outq, 2)))
workers.append(Process(target=connectivity_worker, args=(connectivity3_inq, connectivity3_outq, 3)))

for w in workers:
    w.daemon = True
    w.start()
    
with open(exp.get_filename(out_file), "wb") as out:
    log.info("Starting")
    finished = 0
    out.write("removed,diameter,size,node_conn0_mean,node_conn0_se,node_conn1_mean,node_conn1_se,node_conn2_mean,node_conn2_se,node_conn3_mean,node_conn3_se,node_conn_pairs,failed,high_betweenness,node_count,rewire_f,butterfly_m,failure_type\n")
    while finished < node_count:
        log.info("Iteration {}".format(finished))
        log.info("  Finding betweenness")
        label, centrality = failure_outq.get()
        log.info("  Finding diameter")
        diameter = diameter_outq.get()
        log.info("  Finding size")
        size = size_outq.get()
        log.info("  Finding 0-connectivity")
        node_conn0_mean, node_conn0_se = connectivity0_outq.get()
        log.info("  Finding 1-connectivity")
        node_conn1_mean, node_conn1_se = connectivity1_outq.get()
        log.info("  Finding 2-connectivity")
        node_conn2_mean, node_conn2_se = connectivity2_outq.get()
        log.info("  Finding 3-connectivity")
        node_conn3_mean, node_conn3_se = connectivity3_outq.get()
        log.info("  Writing row")
        row = [finished, diameter, size, node_conn0_mean, node_conn0_se, node_conn1_mean, node_conn1_se, node_conn2_mean, node_conn2_se, node_conn3_mean, node_conn3_se, num_conn_pairs, label, centrality, node_count, rewire_f, butterfly_m,"targeted"]
        out.write(",".join([str(d) for d in row]) + "\n")
        out.flush()
        finished += 1
        if centrality == 0:
            break
log.info("Finished successfully")


# In[ ]:




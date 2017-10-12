
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
from networkx.algorithms.centrality.betweenness import betweenness_centrality
from networkx.algorithms.distance_measures import diameter
import numpy as np
import elp_networks as elpnet
import elp_networks.algorithms as elpalg
import logbook


# In[ ]:

rewire_f = 0.1
butterfly_m = 7
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

def do_centrality_work(g):
    centralities = betweenness_centrality(g, normalized=False)
    v, c = max(centralities.iteritems(), key=lambda x: x[1])
    return v, c

def centrality_worker(graph_q, component_inq, centrality_outq):
    while True:
        g = graph_q.get()
        component_inq.put(g)
        v, c = do_centrality_work(g)
        centrality_outq.put((v,c))
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

graph_q = Queue()
centrality_outq = Queue()
component_inq = Queue()
diameter_inq = Queue()
diameter_outq = Queue()
size_inq = Queue()
size_outq = Queue()

exp = logbook.Experiment(exp_name, suffix=exp_suffix)
log = exp.get_logger()

log.info("Rewiring graph")
g = nx.Graph(edge_list)
rewire_butterfly(g, rewire_f, butterfly_m)
graph_q.put(g)

log.info("Starting workers")
workers = []
workers.append(Process(target=centrality_worker, args=(graph_q, component_inq, centrality_outq)))
workers.append(Process(target=component_worker, args=(component_inq, diameter_inq, size_inq)))
workers.append(Process(target=diameter_worker, args=(diameter_inq, diameter_outq)))
workers.append(Process(target=size_worker, args=(size_inq, size_outq)))

for w in workers:
    w.daemon = True
    w.start()
    
with open(exp.get_filename(out_file), "wb") as out:
    log.info("Starting")
    finished = 0
    out.write("removed,diameter,size,failed,high_betweenness,node_count,rewire_f,butterfly_m\n")
    while finished < node_count:
        log.info("Iteration {}".format(finished))
        log.info("  Finding betweenness")
        label, centrality = centrality_outq.get()
        log.info("  Finding diameter")
        diameter = diameter_outq.get()
        log.info("  Finding size")
        size = size_outq.get()
        log.info("  Writing row")
        row = [finished, diameter, size, label, centrality, node_count, rewire_f, butterfly_m]
        out.write(",".join([str(d) for d in row]) + "\n")
        out.flush()
        finished += 1
        if centrality == 0:
            break
log.info("Finished successfully")


# In[ ]:




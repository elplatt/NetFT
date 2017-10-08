
# coding: utf-8

# In[ ]:

get_ipython().magic(u'pylab inline')
import os
import random
import re
import sys
import time
from multiprocessing import Process, Queue
import networkx as nx
import networkx.algorithms.centrality as nxcent
import networkx.algorithms.distance_measures as nxdist
import networkx.algorithms.components as nxcomp
import numpy as np
import elp_networks as elpnet
import elp_networks.algorithms as elpalg
import logbook


# In[ ]:

random.seed(hash('''
    Build a man a fire, and he'll be warm for a day.
    Set a man on fire, and he'll be warm for the rest of his life.
                                                –Terry Pratchett
'''))


# In[ ]:

try:
    job_id = os.environ["PBS_ARRAYID"]
    exp_name = exp_name
except KeyError:
    job_id = 0

net_file = "external/as20000102.csv"
exp_name = "router_random " + str(job_id)
exp_ts = str(time.time())


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

def do_failure_work(edge_list):
    sources, targets = zip(*edge_list)
    nodes = set(sources) | set(targets)
    failed = random.choice(list(nodes))
    return failed

def failure_worker(edges_q, component_inq, failure_outq):
    while True:
        edge_list = edges_q.get()
        component_inq.put(edge_list)
        v = do_failure_work(edge_list)
        failure_outq.put(v)
        next_edges = [(s,t) for s,t in edge_list if s != v and t != v]
        if len(next_edges) > 0:
            edges_q.put(next_edges)


# In[ ]:

def do_component_work(edge_list):
    g = nx.Graph(edge_list)
    return list(nxcomp.connected_components(g))

def component_worker(component_inq, diameter_inq, size_inq):
    while True:
        edge_list = component_inq.get()
        components = do_component_work(edge_list)
        diameter_inq.put( (components, edge_list) )
        size_inq.put(components)


# In[ ]:

def do_diameter_work(components, edge_list):
    giant_nodes = set(max(components, key=len))
    giant_edges = []
    for source, target in edge_list:
        if source in giant_nodes and target in giant_nodes:
            giant_edges.append( (source, target) )
    g = nx.Graph(giant_edges)
    return nxdist.diameter(g)

def diameter_worker(diameter_inq, diameter_outq):
    while True:
        components, edge_list = diameter_inq.get()
        diameter = do_diameter_work(components, edge_list)
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

edges_q = Queue()
failure_outq = Queue()
component_inq = Queue()
diameter_inq = Queue()
diameter_outq = Queue()
size_inq = Queue()
size_outq = Queue()

edges_q.put(edge_list)

workers = []
workers.append(Process(target=failure_worker, args=(edges_q, component_inq, failure_outq)))
workers.append(Process(target=component_worker, args=(component_inq, diameter_inq, size_inq)))
workers.append(Process(target=diameter_worker, args=(diameter_inq, diameter_outq)))
workers.append(Process(target=size_worker, args=(size_inq, size_outq)))

for w in workers:
    w.daemon = True
    w.start()
    
exp = logbook.Experiment(exp_name)
log = exp.get_logger()
with open(exp.get_filename("targeted_router.csv"), "wb") as out:
    log.info("Starting")
    finished = 0
    out.write("uid,removed,diameter,size,failed,node_count\n")
    while finished < node_count:
        log.info("Iteration {}".format(finished))
        log.info("  Finding failed node")
        label = failure_outq.get()
        log.info("  Finding diameter")
        diameter = diameter_outq.get()
        log.info("  Finding size")
        size = size_outq.get()
        log.info("  Writing row")
        uid = str(exp_ts) + '-' + str(job_id)
        row = [uid, finished, diameter, size, label,node_count]
        out.write(",".join([str(d) for d in row]) + "\n")
        out.flush()
        finished += 1
log.info("Finished successfully")


# In[ ]:

exp.start_ts


# In[ ]:




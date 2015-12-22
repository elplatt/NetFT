import math

import networkx as nx

def to_nx(nodes, edges):
    G = nx.Graph()
    G.add_nodes_from(nodes)
    G.add_edges_from(edges)
    return G

class Network(object):
    
    def __init__(self):
        pass
    
    @classmethod
    def makeGraph(cls, m):
        net = cls(m)
        G = to_nx(net.nodes, net.edges)
        del net
        return G

class Cube(Network):
    
    def __init__(self, m):
        '''Create an m-dimensional cube.'''
        # Create nodes
        self.nodes = set(range(0,pow(2,m)))
        # Create edges
        self.edges = set()
        basis = [pow(2, i) for i in range(m)]
        for node in self.nodes:
            # Add an edge for each bit, but only to nodes with higher ids
            # to avoid double counting.
            for i in xrange(m):
                bit = basis[i]
                if node & bit == 0:
                    self.edges.add(frozenset((node, node | bit)))
    
    @classmethod
    def iternodes(cls, m):
        return xrange(pow(2,m))
    
    @classmethod
    def iterneighbors(cls, m, v):
        for i in xrange(m):
            yield v ^ (1 << i)
    
    @classmethod
    def pathlength_counts(cls, m):
        lengths = range(m + 1)
        counts = [math.factorial(m) / math.factorial(h) / math.factorial(m-h) for h in lengths]
        return (lengths, counts)

class Butterfly(Network):
    
    def __init__(self, m):
        '''Create an m-dimensional butterfly network.'''
        self.nodes = set([(0,0)])
        self.edges = set()
        in_level_max = pow(2, m)
        for level in range(m):
            for in_level in range(in_level_max):
                node = (level, in_level)
                self.nodes.add(node)
                down = ((level + 1) % m, in_level)
                down_right = ((level + 1) % m, in_level ^ (1 << level))
                if node != down:
                    self.edges.add(frozenset((node, down)))
                if node != down_right:
                    self.edges.add(frozenset((node, down_right)))

class NestedClique(Network):
    
    def __init__(self, m):
        '''Create an m-dimensional nested clique.'''
        N = NestedClique._N(m)
        self.nodes = set()
        self.edges = set()
        for z in range(N):
            v = NestedClique._z2v(z, m)
            self.nodes.add(tuple(v))
            # Only add edges for odd nodes to prevent double counting
            if z % 2 == 1:
                for w in NestedClique.neighbors(v):
                    self.edges.add(frozenset( (tuple(v), w) ))
    
    @classmethod
    def neighbors(cls, v):
        '''Returns an iterator of the neighbors of a given node.'''
        # See paper notebook ELP-UM-001 p.51
        m = len(v)
        z = cls._v2z(v)
        w = list(v)
        zz = 0
        # Create level-k edges by changing lowest k values
        for i in range(m):
            Ni = NestedClique._N(i)
            if z % 2 == 1:
                w[i] = (w[i] - 1 - zz) % (Ni + 1)
            else:
                w[i] = (w[i] + 1 + ((zz - 1) % Ni) ) % (Ni + 1)
            zz += Ni * v[i]
            yield tuple(w)
    
    @classmethod
    def _v2z(cls, v):
        '''Convert from vertex to integer.'''
        z = 0
        for (i, vi) in enumerate(v):
            z += cls._N(i) * vi
        return z
    
    @classmethod
    def _z2v(cls, z, m):
        '''Convert from integer to vertex.'''
        i = 0
        v = []
        zz = z
        while zz > 0 or i < m:
            N = cls._N(i)
            nextN = cls._N(i + 1)
            remainder = zz % nextN
            zz -= remainder
            v.append(int(remainder/N))
            i += 1
        return v
    
    @classmethod
    def _N(cls, i):
        try:
            return cls._N_cache[i]
        except AttributeError:
            cls._N_cache = [1]
        except IndexError:
            pass
        last = cls._N(i - 1)
        result = last * (last + 1)
        cls._N_cache.append(result)
        return result
    
if __name__ == '__main__':
    import pprint
    g = Butterfly(2)
    pprint.pprint(g.nodes)
    pprint.pprint(g.edges)
    
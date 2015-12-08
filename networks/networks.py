
class Cube(object):
    
    def __init__(self, m):
        '''Create an m-dimensional cube.'''
        # Create nodes
        self.nodes = set(range(0,pow(2,m)))
        # Create edges
        self.edges = set()
        basis = [pow(2, x) for x in range(0,m)]
        for node in self.nodes:
            # Add an edge for each bit, but only to nodes with higher ids
            # to avoid double counting.
            for bit in basis:
                if node & bit == 0:
                    self.edges.add(frozenset((node, node | bit)))

class Butterfly(object):
    
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
                self.edges.add(frozenset((node, down)))
                self.edges.add(frozenset((node, down_right)))

class NestedClique(object):
    
    def __init__(self, m):
        '''Create an m-dimensional nested clique.'''
        (self.nodes, self.edges) = self._make(m)

    def _make(self, m):
        if m == 0:
            nodes = set([()])
            edges = set([])
        elif m == 1:
            nodes = set([(0,), (1,)])
            edges = set([frozenset([(0,), (1,)])])
        else:
            pass
        return (nodes, edges)
    
if __name__ == '__main__':
    import pprint
    g = Butterfly(2)
    pprint.pprint(g.nodes)
    pprint.pprint(g.edges)
    
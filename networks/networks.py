
class Cube(object):
    
    def __init__(self, m):
        '''Create an m-dimensional cube.'''
        # Create nodes
        self.nodes = range(0,pow(2,m))
        # Create edges
        self.edges = []
        basis = [pow(2, x) for x in range(0,m)]
        for node in self.nodes:
            # Add an edge for each bit, but only to nodes with higher ids
            # to avoid double counting.
            for bit in basis:
                if node & bit == 0:
                    self.edges.append(set((node, node | bit)))

if __name__ == '__main__':
    import pprint
    c = Cube(2)
    print(c.nodes)
    print(c.edges)
    
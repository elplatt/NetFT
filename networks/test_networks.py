import unittest
import networks

square_nodes = set(range(4)) 
square_edges = set([
    frozenset((0,1)), frozenset((1,3)), frozenset((3,2)), frozenset((2,0))
])

butterfly_nodes = set([
    (0, 0)
    , (0, 1)
    , (0, 2)
    , (0, 3)
    , (1, 0)
    , (1, 1)
    , (1, 2)
    , (1, 3)
])
butterfly_edges = set([
    frozenset(((0, 0), (1, 0)))
    , frozenset(((0, 0), (1, 1)))
    , frozenset(((0, 1), (1, 0)))
    , frozenset(((0, 1), (1, 1)))
    , frozenset(((0, 2), (1, 2)))
    , frozenset(((0, 2), (1, 3)))
    , frozenset(((0, 3), (1, 2)))
    , frozenset(((0, 3), (1, 3)))
    , frozenset(((0, 3), (1, 1)))
    , frozenset(((0, 1), (1, 3)))
    , frozenset(((0, 0), (1, 2)))
    , frozenset(((0, 2), (1, 0)))
])

class TestCube(unittest.TestCase):
    
    def test_base(self):
        cube = networks.Cube(0)
        self.assertEqual(cube.nodes, set((0,)))
        self.assertEqual(cube.edges, set())
        
    def test_square(self):
        cube = networks.Cube(2)
        self.assertEqual(cube.nodes, square_nodes)
        self.assertEqual(cube.edges, square_edges)

class TestButterfly(unittest.TestCase):
    
    def test_base(self):
        net = networks.Butterfly(0)
        self.assertEqual(net.nodes, set([(0,0)]))
        self.assertEqual(net.edges, set())

    def test_two(self):
        net = networks.Butterfly(2)
        self.assertEqual(net.nodes, butterfly_nodes)
        self.assertEqual(net.edges, butterfly_edges)

class TestNestedClique(unittest.TestCase):
    
    def test_N(self):
        net = networks.NestedClique(0)
        self.assertEqual(net._N(4), 1806)
    
    def test_z2v(self):
        z = 0*1 + 2*2 + 3*6
        self.assertEqual(networks.NestedClique._z2v(z), [0, 2, 3])
    
    def test_base(self):
        net = networks.NestedClique(0)
        self.assertEqual(net.nodes, set([()]))
        self.assertEqual(net.edges, set())
        
    def test_one(self):
        net = networks.NestedClique(1)
        self.assertEqual(net.nodes, set([(0,), (1,)]))
        self.assertEqual(net.edges, set([ frozenset([(0,), (1,)]) ]))

if __name__ == '__main__':
    unittest.main()
    
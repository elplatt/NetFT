import unittest
import networks

square_nodes = set(range(4)) 
square_edges = set([
    frozenset((0,1)), frozenset((1,3)), frozenset((3,2)), frozenset((2,0))
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

if __name__ == '__main__':
    unittest.main()
    
# Network generators

This package generates different kinds of networks.
All objects have a `nodes` list containing integer node ids,
as well as an `edges` list containing 2-sets of node ids.

Currently available networks are:
* Cube(m): An m-dimensional cube

## Example usage
Creating a generator:

    import networks
    net = networks.Cube(2)
    
    print net.nodes
    #=> [0, 1, 2, 3]
    
    print net.edges
    #=> [set([0, 1]), set([0, 2]), set([1, 3]), set([2, 3])]

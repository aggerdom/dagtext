import pytest
from mock import MagicMock
from dagtext import graphModel


def create_graph(elements, patch_lookup=False):
    """
    Instantiate a DocumentModel from a list of nodes & edges/paths.
    Nodes should be specified as either integers or strings.
    Paths/Edges should be provided as a tuple or list.

    :param elements: iterable containing integers/strings iterable of nodes & edges
    :type elements: list or tuple
    :param patch_lookup: If True, will attach a reference dictionary as <instance>.reference
    :type patch_lookup: bool
    :return: DocumentGraph with the elements described
    :rtype: graphModel.DocumentGraph


    EXAMPLE

        #   /-> a
        # b -> c -> e
        # g -> f

        >>> elements = ('a', ('b','c','e'), ('g','f'))
        >>> doc = create_graph(elements, patch_lookup=True)
        >>> lookup = doc.lookup
        >>> lookup
        {'e': 21, 'b': 19, 'g': 22, 'a': 0, 'c': 20, 'f': 23}
        >>> doc.is_dag()
        True
        >>> sorted(doc.edges)
        [(7, 8), (8, 9), (10, 11)]
        >>> g = doc.digraph_from_titles()
        >>> sorted(g.nodes())
        ['a','b','c','e','f','g']
        >>> g.edges()

    """
    doc = graphModel.DocumentGraph()
    lookup = {}
    for element in elements:
        # single element => node
        # two or more elements => edge or path
        if type(element) in (int, str):
            lookup[element] = doc.add_node(text=str(element), title=str(element))
        elif type(element) in (list, tuple):
            if len(element) <= 1:
                raise ValueError("Paths must contain at least two elements")

            for head, tail in zip(element[:-1], element[1:]):
                if any(type(part) not in (int, str) for part in (head, tail)):
                    raise ValueError("Values w/in a path/edge must be ints or str")
                # add the node if it hasn't occured previously
                if head not in lookup:
                    lookup[head] = doc.add_node(text=str(head), title=str(head))
                if tail not in lookup:
                    lookup[tail] =  doc.add_node(text=str(tail), title=str(tail))
                doc.add_edge(lookup[head], lookup[tail])
    if patch_lookup:
        doc.lookup = lookup
    return doc


@pytest.fixture(scope='function')
def reset_nodecount():
    import itertools
    graphModel.NODECOUNT = itertools.count()


def test_test_create_graph(reset_nodecount):
    elements = ('a', ('b', 'c'))
    doc = create_graph(elements, patch_lookup=True)
    lookup = doc.lookup

    # check it creates it correctly
    g = doc.digraph_from_titles()
    assert all(g.has_node(n) for n in ('a', 'b', 'c'))
    assert g.has_edge('b', 'c')

    # check that it updates
    lookup['e'] = doc.add_node(title="e", text="e")
    doc.add_edge(lookup["b"], lookup["e"])
    g = doc.digraph_from_titles()
    assert g.has_node('e')
    assert g.has_edge('b', 'e')

    # check that errors are correctly thrown
    malformed = [('a', ('b', 'c'), ()),  # empty edge
                 ('a', ('b', 'c', 'e'), ('a',)),  # edge w/ one member
                 ('a', ('b', ('c', 'd'))),  # edge w/ nested edge
                 ]
    for malexp in malformed:
        with pytest.raises(ValueError):
            print(malexp)
            doc = create_graph(malexp, patch_lookup=True)


@pytest.fixture(scope='function')
def instantiate_graph(reset_nodecount):
    doc = graphModel.DocumentGraph()
    return doc


@pytest.fixture(scope='function')
def instantiate_dag():
    # a -> b -> c -> e
    #      \ -> d
    elements = (('a', 'b', 'c', 'e'),
                ('b', 'd'))
    doc = create_graph(elements, patch_lookup=True)
    lookup = doc.lookup
    return doc, lookup


@pytest.fixture(scope='function')
def instantiate_nondag(instantiate_graph):
    # a -> b -> c -> e
    #      \ -> d -> a
    doc = instantiate_graph
    a = doc.add_node(title='a')
    b = doc.add_node(title='b')
    c = doc.add_node(title='c')
    d = doc.add_node(title='d')
    e = doc.add_node(title='e')
    for edge in ((a, b), (b, c), (c, e), (b, d), (d, a)):
        doc.add_edge(*edge)
    return doc


def test_dag(reset_nodecount):
    dag = instantiate_dag


def add_n_nodes(docgraph, n):
    added_ids = [docgraph.add_node(text="added node") for _ in range(n)]
    return added_ids


def test_graph_instantiation(instantiate_graph):
    graph = instantiate_graph
    assert hasattr(graph, "G")
    assert isinstance(graph.G, graphModel.nx.DiGraph)


def test_node_instantiation(reset_nodecount):
    graph = graphModel.DocumentGraph()
    nodeids = add_n_nodes(graph, 1)
    assert nodeids[0] == 0


def test_split_default():
    doc = graphModel.DocumentGraph()
    node0 = doc.add_node(title="FirstNode", text="second node")
    assert node0 in doc.G.node

    # split the node
    node1, node2 = doc.split_node(node0, 1)

    # test for remove and node addition
    assert node0 not in doc.G.node
    assert len(doc.G.node) == 2
    assert node1 in doc.G.node
    assert node2 in doc.G.node

    # test node attributes
    title1, title2 = doc.G.node[node1]['title'], doc.G.node[node2]['title']
    assert (title1 == doc[node1].title) and (title2 == doc[node2].title)

    # test for creation of an edge from the head to the tail
    # (The default)
    assert (node1, node2) in doc.G.out_edges(node1)
    assert (node1, node2) in doc.G.in_edges(node2)
    return doc.G.node


class TestGraphModelGetter:
    def test_node_getter(self):
        g = graphModel.DocumentGraph()
        n0 = g.add_node(title="Foo", text="Hello world")
        n1 = g.add_node(title="Bar", text="from Alex")
        g.add_edge(n0, n1)
        edge = g[(n0, n1)]
        assert edge.head == n0 and edge.tail == n1

    def test_edge_getter(self):
        g = graphModel.DocumentGraph()
        n1 = g.add_node(title="Foo", text="Hello world")
        assert g[n1].title == 'Foo'
        assert g[n1].text + "!" == "Hello world!"
        assert g[n1].text + g[n1].text == "Hello worldHello world"

    def test_edge_attribute(self, reset_nodecount):
        doc = create_graph((('a', 'b', 'c', 'd', 'e'),)
                           , patch_lookup=True)
        for edge in  (('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')):
            edgeids = (doc.lookup[edge[0]], doc.lookup[edge[1]])
            assert edgeids in doc.edges

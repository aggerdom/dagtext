import pytest
from mock import MagicMock
from dagtext import graphModel, signal_tester


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
        ['a', 'b', 'c', 'e', 'f', 'g']
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
                    lookup[tail] = doc.add_node(text=str(tail), title=str(tail))
                doc.add_edge(lookup[head], lookup[tail])
    if patch_lookup:
        doc.lookup = lookup
    return doc


@pytest.fixture(scope='function')
def reset_nodecount():
    import itertools
    graphModel.NODECOUNT = itertools.count()


def test_test_create_graph(reset_nodecount):
    """
    Tests create_graph function used for testing.

    :param reset_nodecount:
    :type reset_nodecount:
    :return:
    :rtype:
    """
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
def instantiate_empty_graph(reset_nodecount):
    doc = graphModel.DocumentGraph()
    return doc


def test_graph_instantiation(instantiate_empty_graph):
    graph = instantiate_empty_graph
    assert hasattr(graph, "G")
    assert isinstance(graph.G, graphModel.nx.DiGraph)


@pytest.fixture(scope='function')
def instantiate_dag(reset_nodecount) -> graphModel.DocumentGraph:
    # a -> b -> c -> e
    #      \ -> d
    elements = (('a', 'b', 'c', 'e'),
                ('b', 'd'))
    doc = create_graph(elements, patch_lookup=True)
    assert doc.is_dag()
    lookup = doc.lookup
    return doc


@pytest.fixture(scope='function')
def instantiate_nondag(reset_nodecount) -> graphModel.DocumentGraph:
    # a -> b -> c -> e
    #      \ -> d -> a
    elements = (('a', 'b', 'c', 'e'),
                ('b', 'd'),
                ('d', 'a'))
    doc = create_graph(elements, patch_lookup=True)
    assert not doc.is_dag()
    return doc


class TestGraph:
    def test_init(self):
        doc = graphModel.DocumentGraph()
        assert hasattr(doc, "G")

    def test_from_yaml(self, reset_nodecount):
        doc = graphModel.DocumentGraph()
        n1 = doc.add_node('n1', 'n1')
        assert 0  # TODO: fill in test

    def test_to_yaml(self):
        assert 0  # TODO: fill in test

    # test attributes
    def test_nodes(self, reset_nodecount):
        doc = graphModel.DocumentGraph()
        nodes = list("abcdefg")
        nodeids = [doc.add_node(text=n, title=n) for n in nodes]
        assert nodeids == list(range(7))
        assert isinstance(doc.nodes, frozenset)  # check return type
        assert all(nid in doc.nodes and nid in doc.G.nodes()
                   for nid in nodeids)
        assert sorted(nodeids) == sorted(doc.nodes)
        removed_node = nodeids.pop()
        doc.remove_node(removed_node)
        assert removed_node not in doc.nodes

    def test_edges(self, reset_nodecount):
        doc = graphModel.DocumentGraph()
        nodes = list("abcdefg")
        nodeids = [doc.add_node(text=n, title=n) for n in nodes]
        # initial pass, check that their found in the index
        for (a, b) in zip(nodeids[:1], nodeids[1:]):
            doc.add_edge(a, b)
        for (a, b) in zip(nodeids[:1], nodeids[1:]):
            assert (a, b) in doc.edges
        assert isinstance(doc.edges, frozenset)

    def test_get_item(self):
        doc = graphModel.DocumentGraph()
        nodes_text = list("abcdefg")
        nodeids = [doc.add_node(text=n, title=n) for n in nodes_text]
        instantiated_edges = []
        for (a, b) in zip(nodeids[:1], nodeids[1:]):
            doc.add_edge(a, b)
            instantiated_edges.append((a, b))

        # test doc[nodeid] -> Node
        nodeinstances = [doc[nid] for nid in nodeids]
        assert all(isinstance(node, graphModel.Node) for node in nodeinstances)
        # assert all(hasattr(nodeinstances[0],a) for a in ('text','title','nodeid'))

        # test doc[(head1,head2)] -> Edge
        for a, b in instantiated_edges:
            assert (a, b) in doc.edges
            assert isinstance(doc[(a, b)], graphModel.Edge)

    # TODO: what to do with setitem
    def test_set_item(self):
        assert 0  # TODO: fill in test

    # test methods
    def test_add_node(self, reset_nodecount):
        doc = graphModel.DocumentGraph()
        sig_created = doc.sig_node_created
        sig_removed = doc.sig_node_removed
        recording = signal_tester.SignalRecording(signals=(sig_created, sig_removed))

        # create a node
        node1 = doc.add_node(title="Node 0", text="I'm the first node!")
        assert node1 == 0

        # split that node
        node1head, node1tail = doc.split_node(node1, 7)
        assert [(node in doc.nodes) for node in (node1, node1head, node1tail)] == [False, True, True]

        # Check that things proceeded in the expected way
        signal_sequence = [item[0] for item in recording]
        from pprint import pprint
        pprint(signal_sequence)
        assert signal_sequence == [sig_created,  # node1
                                   sig_created,  # node1head
                                   sig_created,  # node1tail
                                   sig_removed]  # rem node 1

        sig, source, nodeid = recording[-1]['nodeid']
        assert recording[-1][-1]['nodeid'] == ''

        # Check that it munges arguments for title and text to strings
        node2 = doc.add_node(title="Node 1", text=0)
        assert doc[node2].text == '0'

    def test_remove_node(self, instantiate_dag):
        doc = instantiate_dag
        doc.remove_node(0)
        assert 0 not in doc.nodes
        with pytest.raises(KeyError):
            doc.remove_node(0)  # catch networkX error and return a key error instead

    def test_add_edge(self):
        doc = graphModel.DocumentGraph()
        nodes_text = list("abcdefg")
        nodeids = [doc.add_node(text=n, title=n) for n in nodes_text]
        instantiated_edges = []
        for (a, b) in zip(nodeids[:1], nodeids[1:]):
            doc.add_edge(a, b)
            instantiated_edges.append((a, b))
        assert all((a, b) in doc.edges for a, b in instantiated_edges)
        # nodeid not in graph
        with pytest.raises(ValueError):
            doc.add_edge(20, 1)
        with pytest.raises(ValueError):
            doc.add_edge(1, 20)

        # illegal argument type
        with pytest.raises(ValueError):
            doc.add_edge("a", "b")

    def test_remove_edge(self):
        assert 0  # TODO: fill in test

    def test_split_node(self):
        assert 0  # TODO: fill in test

    def test_split_node_defaults(self, reset_nodecount):
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

    def test_join_nodes(self):
        assert 0  # TODO: fill in test

    def test_dag(self, instantiate_dag):
        # a -> b -> c -> e
        #      \ -> d
        dag = instantiate_dag  # type: graphModel.DocumentGraph
        assert dag.is_dag()

        # a -> b -> c -> e -> f
        #      \ -> d
        dag.lookup['f'] = dag.add_node(title='f', text='f')
        assert dag.is_dag()
        dag.add_edge(dag.lookup['e'], dag.lookup['f'])
        assert dag.is_dag()

        # make it no longer a dag
        #      a -> b -> c -> e -> f -> c
        #      \ -> d
        dag.add_edge(dag.lookup['f'], dag.lookup['c'])
        assert not dag.is_dag()

        # remove f (and its incoming and outgoing edges)
        #   to make it a dag again
        dag.remove_node(dag.lookup['f'])
        assert dag.is_dag()

    def test_layout(self):
        assert 0  # TODO: fill in test

    def test_digraph_from_titles(self):
        assert 0  # TODO: fill in test


def add_n_nodes(docgraph, n):
    added_ids = [docgraph.add_node(text="added node") for _ in range(n)]
    return added_ids


def test_node_instantiation(reset_nodecount):
    graph = graphModel.DocumentGraph()
    nodeids = add_n_nodes(graph, 1)
    assert nodeids[0] == 0


class TestGraphModelGetter:
    def test_node_getter(self):
        g = graphModel.DocumentGraph()
        n1 = g.add_node(title="Foo", text="Hello world")
        assert g[n1].title == 'Foo'
        assert g[n1].text + "!" == "Hello world!"
        assert g[n1].text + g[n1].text == "Hello worldHello world"

    def test_edge_getter(self):
        g = graphModel.DocumentGraph()
        n0 = g.add_node(title="Foo", text="Hello world")
        n1 = g.add_node(title="Bar", text="from Alex")
        g.add_edge(n0, n1)
        edge = g[(n0, n1)]
        assert edge.head == n0 and edge.tail == n1

    def test_edge_attribute(self, reset_nodecount):
        doc = create_graph((('a', 'b', 'c', 'd', 'e'),)
                           , patch_lookup=True)
        for edge in (('a', 'b'), ('b', 'c'), ('c', 'd'), ('d', 'e')):
            edgeids = (doc.lookup[edge[0]],
                       doc.lookup[edge[1]])
            assert edgeids in doc.edges

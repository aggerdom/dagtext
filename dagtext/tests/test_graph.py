import pytest
from mock import MagicMock
from dagtext import graphModel


def test_graph_instantiation():
    graph = graphModel.DocumentGraph()
    assert hasattr(graph, "G")
    assert isinstance(graph.G, graphModel.nx.DiGraph)


def test_node_instantiation():
    graph = graphModel.DocumentGraph()
    node = graph.add_node(text="", title="<Node 0>")
    assert node == 0


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

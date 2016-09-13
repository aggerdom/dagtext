import pytest
from mock import MagicMock
from dagtext import graphModel


# def test_graph_instantiation():
#     graph = graphModel.DocumentGraph()
#     assert hasattr(graph,"G")
#     assert isinstance(graph.G, graphModel.nx.DiGraph)
#
# def test_node_instantiation():
#     graph = graphModel.DocumentGraph()
#     node = graphModel.Node(0,text="",title="<Node 0>")

# def test_instantiate():
#     graph = graphModel.DocumentGraph()
#     assert graph.uidcounter == 0
#     assert len(graph.uidLookup)==0
#     node = graph.add_node(text="node1", title=None, nodeid=None)
#
#     # check it's added to lookup
#     assert node.uid in graph.uidLookup
#     assert node.title is not None

class TestModelNode:
    def test_split(self):
        n1 = graphModel.ModelNode(uid=graphModel.uuid.uuid4(),
                                  title="Foo",
                                  text="Hello world")
        assert hasattr(n1, "uid") and hasattr(n1, "title") and hasattr(n1, "text")
        assert "Hello world" == n1.text

        n1a, n1b = n1.split(5)
        assert n1a.text == "Hello"
        assert n1b.text == " world"

    def test_cat(self):
        n1 = graphModel.ModelNode(uid=graphModel.uuid.uuid4(),
                                  title="Foo",
                                  text="Hello world")
        assert n1.cat("!") == "Hello world!"
        print("{!r}".format(n1.cat(n1)))
        assert n1.cat(n1) == "Hello worldHello world"

    def test_join(self):
        n1 = graphModel.ModelNode(uid=graphModel.uuid.uuid4(),
                                  title="Foo",
                                  text="Hello world")
        raise NotImplementedError


class TestDocumentGraph:
    def test_add_node(self):
        pass

    def test_split_node(self):
        pass
        # test that the

    def test_join_node(self):
        pass

    def test_is_dag(self):
        pass

    def test_dump(self):
        pass
# from dagtext.signals import *
import itertools

import networkx as nx

NODECOUNT = itertools.count()
# TODO: move to config
DOCGRAPHSAVELOC = "C:/users/alex/.dagtext/lastopen.yml"


class DocumentGraph(object):
    """Graph that manages nodes and edges"""

    def __init__(self, graph=None):
        super(DocumentGraph, self).__init__()
        if graph is None:
            graph = nx.DiGraph()
        self.G = graph

    ## Methods to persist graph
    @classmethod
    def from_yaml(cls, ymlfilepath):
        """
        Create a document graph instance from a dump of a graph created by nx.write_yaml.

        :param ymlfilepath: path to yml file created by using nx.dump(G,ymlfilepath)
        :type ymlfilepath: str
        :return: Loaded document graph
        :rtype: DocumentGraph
        """
        G = nx.read_yaml(ymlfilepath)
        return DocumentGraph(graph=G)

    def dump_to_yaml(self, filepath=DOCGRAPHSAVELOC):
        nx.write_yaml(self.G, filepath)

    ## Node management methods
    def add_node(self, text="", title=None):
        """
        Creates a new node in the graph instance with the specified paramaters, and adds it to the graph instances
        uidLookup.

        :param text: Text content of the node
        :type text: str
        :param title: Title of the node that will display on the canvas
        :type title: str
        :return: The ID of the newly created node
        :rtype: int
        """
        # nodeid = uuid.uuid4()
        nodeid = next(NODECOUNT)
        if title is None:
            title = "<Node {}>".format(nodeid)

        nodeattrs = dict(text=text, title=title)
        self.G.add_node(nodeid, nodeattrs)
        return nodeid

    def add_edge(self, node1, node2):
        """
        Create an directed edge from node1 to node2.
        """
        self.G.add_edge(node1, node2)

    def get_node(self, nodeid):
        pass

    def get_edges(self, nodeid):
        return {"in" : self.G.in_edges(nodeid),
                "out": self.G.out_edges(nodeid)}

    ## Graph Rewriting/Manipulation Methods
    def split_node(self, nodeid, location,
                   in2head=True, in2tail=False,
                   head2tail=True, head2out=False,
                   tail2out=True, in2out=False):
        """
        Split a node at a given location, and connect edges as specified in the keyword arguments.

        :rawtext:

                       +----+       +-----------------------+           +----+
                       |Node| ----> |        "head"         | +-------> |Node|
                       +----+       |                       |           +----+
                 +----+             | - - - location  - - - |
                 |Node| ----------> |                       |              +----+
                 +----+             |        "tail"         | +--------->  |Node|
                                    +-----------------------+              +----+


                +-------------+    +--------------------------+  +----------------+
                     "in"                  node (arg[1])               "out"

        ARGS:
            nodeid (int): Node to be split
            location (int): Index in the node's text to split the node

        KWARGS:
            in2head (bool): If True nodes w/ edges to the original node will point to the first part of the split
            in2tail (bool): If True nodes w/ edges to the original node will point to the second part of the split
            head2tail (bool): If True nodes the first part of the split will point to the second part of the split
            head2out (bool): If True, the first part of the split will have edges to all nodes w/ edges from the
                             original node
            tail2out (bool): If True nodes w/ edges to the original node will point to the second part of the split
            in2out (bool): If True nodes w/ edges to the original node will point to all nodes w/ edges from the
                             original node

        RETURNS:
            (head,tail)
        """

        text = self.G.node[nodeid]["text"]
        title = self.G.node[nodeid]["title"]
        texthead, texttail = text[:location], text[location:]

        # create two new nodes from the contents
        head = self.add_node(text=texthead, title=title + " (1)")
        tail = self.add_node(text=texttail, title=title + " (2)")

        # link them up
        incoming = [edge[0] for edge in self.G.in_edges(nodeid)]
        outgoing = [edge[1] for edge in self.G.out_edges(nodeid)]
        if in2head:
            for upnode in incoming:
                self.add_edge(upnode, head)
        if in2tail:
            for upnode in incoming:
                self.add_edge(upnode, tail)
        if head2tail:
            self.add_edge(head, tail)
        if head2out:
            for downnode in outgoing:
                self.add_edge(head, downnode)
        if tail2out:
            for downnode in outgoing:
                self.add_edge(tail, downnode)
        if in2out:
            for upnode in incoming:
                for downnode in outgoing:
                    self.add_edge(upnode, downnode)

        # remove the original node
        self.G.remove_node(nodeid)
        return head, tail

    def join_nodes(self, node1, node2):
        # newtitle = "[{} + {}]".format(node)
        raise NotImplementedError

    def is_dag(self):
        return nx.is_directed_acyclic_graph(self.G)

    def layout(self, canvas_width, canvas_height, layoutMethod="spring"):
        # calculate new node positions
        width = canvas_width
        height = canvas_height

        # center of canvas
        canvas_center = (int(.5 * width), int(.5 * height))
        minreq = min(width, height)
        if layoutMethod == "circular":
            pos = nx.circular_layout(
                self.G, scale=.45 * minreq, center=canvas_center)
        elif layoutMethod == "spring":
            pos = nx.spring_layout(
                self.G, scale=.4 * minreq, center=canvas_center)
        elif layoutMethod == "shell":
            pos = nx.shell_layout(
                self.G, scale=.4 * minreq, center=canvas_center)
        elif layoutMethod == 'spectral':
            pos = nx.spectral_layout(
                self.G, scale=.4 * minreq, center=canvas_center)
        else:
            raise NotImplementedError
        return pos


def test_split():
    doc = DocumentGraph()
    node1 = doc.add_node(title="FirstNode", text="second node")
    assert node1 in doc.G.node
    # split the node
    node2, node3 = doc.split_node(node1, 1)
    # test for remove and node addition
    assert node1 not in doc.G.node
    assert len(doc.G.node) == 2
    assert node2 in doc.G.node
    assert node3 in doc.G.node
    # test for creation of an edge from the head to the tail
    assert (node2, node3) in doc.G.out_edges(node2)
    assert (node2, node3) in doc.G.in_edges(node3)

    return doc.G.node

if __name__ == "__main__":
    test_split()

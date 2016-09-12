# from dagtext.signals import *
from signals import *
import networkx as nx
import uuid
import yaml
import itertools
from collections import namedtuple


def listener(source, **kws):
    print("(listener) recieved from", source, ",", kws)


for s in SIGNALS:
    SIGNALS[s].connect(listener)


class ModelNode(namedtuple("ModelNode", ["uid", "title", "text"])):
    """
    Class that contains that basic information for a node in a document.

    <node>.uid = A unique identifier that specifies the identity of the node
        typically will be assigned using uuid.uuid4.
    <node>.title = A name for the node, typically used in its handle on the
        graph in the gui.
    <node>.text = The contents of a node
    """
    __slots__ = ()

    def __str__(self):
        return self.text

    def split(self, index):
        """
        Creates two new nodes consisting of self.text split at a given index.

        SIGNALS:
            SIGNAME: signals.SIGNALS["nodeSplit"]
            SIGSOURCE: <node being split>
            SIGDATA: created=(headnode, tailnode)

        :param index:
        :type index: int
        :return: headnode, tailnode
        :rtype: tuple
        """

        # create two new nodes from the contents
        head, tail = self.text[:index], self.text[index:]
        node1 = ModelNode(uid=uuid.uuid4(),
                          title=self.title + " (1)",
                          text=head)
        node2 = ModelNode(uid=uuid.uuid4(),
                          title=self.title + " (2)",
                          text=tail)

        # notify the rest of the application of the node splitting
        splitsignal = SIGNALS["nodeSplit"]
        splitsignal.send(self, created=(node1, node2))

        return node1, node2

    def cat(self, other):
        """
        self.text + <somestring>

        If other is a string, returns self.text+other
        If other is a node, returns self.text+other.text
        """
        if isinstance(other, ModelNode):
            return self.text + other.text
        elif isinstance(other, str):
            return self.text + other

    def __repr__(self):
        return "Node(uid:{},title:{},text:{})".format(self.uid, self.title, self.text)


class DocumentGraph(object):
    """Graph that manages nodes and edges"""

    def __init__(self, graph=None):
        super(DocumentGraph, self).__init__()
        if graph is None:
            self.G = nx.DiGraph()
            self.uidLookup = {}
        else:
            self.G = graph
            self.uidLookup = {node.uid: node for node in self.G.node.keys()}

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

    def add_node(self, text="", title=None):
        """
        Creates a new node in the graph instance with the specified paramaters, and adds it to the graph instances
        uidLookup.

        :param text: Text content of the node
        :type text: str
        :param title: Title of the node that will display on the canvas
        :type title: str
        :return: The newly created node
        :rtype: Node
        """
        nodeid = uuid.uuid4()
        if title is None:
            title = "<Node {}>".format(nodeid)

        node = ModelNode(nodeid, text=text, title=title)
        self.uidLookup[nodeid] = node
        return node

    def add_edge(self, node1, node2):
        """
        Create an directed edge from node1 to node2.
        """
        self.G.add_edge(node1, node2)

    def split_node(self, node, location,
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
            node (ModelNode): Node to be split
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
        """
        head, tail = node.split(location)
        incoming = [edge[0] for edge in self.G.in_edges(node)]
        outgoing = [edge[1] for edge in self.G.out_edges(node)]
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

    def join_nodes(self, node1, node2):
        raise NotImplementedError

    def dump_to_yaml(self, Gfilepath, Sfilepath):
        # dump the graph to yaml
        nx.write_yaml(self.G, Gfilepath)
        # dump the UID2Node lookup
        yaml.dump(self.uidLookup, open(Sfilepath))

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


if __name__ == "__main__":
    n1 = ModelNode(uid=uuid.uuid4(),
                   title="Foo",
                   text="Hello world")
    n1a, n1b = n1.split(5)

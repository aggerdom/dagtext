# from dagtext.signals import *
import itertools

import networkx as nx
from pprint import pformat
from collections import namedtuple

"""
FILE: graphModel.py
AUTHOR: Alex Gerdom
github username: aggerdom

Description:
    Contains classes and helper functions that implement the logic for the underlying
    datamodel, and provide convenient access in such a way that we don't let the
    networkx.DiGraph instances get out of sync.

Major Classes:
    DocumentGraph:
        Handles interactions with the nx.DiGraph instance
    Node:
        Object (currently namedtuple) that holds node data and provides it through named attributes.
        May later serve as an interface for the DocumentGraph's node handling functions.
    Edge:
        Object (currently namedtuple) that holds node data.
        May later serve as an interface for the DocumentGraph's edge handling functions.

## IMPLEMENTATION NOTES



### Handling of nodeids

In order to ensure that the nodes are being created in a way that we can keep track
of them across different graph instances (perhaps in the case that I decide
to implement subgraphs in the future). Nodes are uniquely identified, by a variable
in graphModel.NODECOUNT that is an instance of itertools.count. The ids will increment
any time a new node is added to the DocumentGraph instance.

:WARNING:
    IF IMPORTING AN EXISTING GRAPH:
        1. All Node ids (and edges) in the new graph should be incremented by next(NODECOUNT)+1
            - When this happens, an appropriate signal from dagtext.signals.py should be called
        2. THIS COUNTER MUST BE INCREMENTED TO THE HIGHEST NODEID + 1
    - Do not try and use nodeids created by this module in a later session
    - The amount this counter increments by can vary by operation w/ some
      incrementing more than 1 if they have intermediate operations on the underlying
      graph. However it should only increase, even with undo operations.

"""

# TODO: move to config
DOCGRAPHSAVELOC = "C:/users/alex/.dagtext/lastopen.yml"
NODECOUNT = itertools.count()
Node = namedtuple("Node", ["nodeid", "title", "text"])
Edge = namedtuple("Edge", ["head", "tail", "attribs"])  # additional attributes will be attribute, value pairs


def update_nodecount(new_point):
    assert isinstance(new_point, int)
    global NODECOUNT
    NODECOUNT = itertools.count(start=new_point)


class DocumentGraph(object):
    """Graph representing document and managing access to the underlying networkx graph.

    :EXAMPLE:
        >>> doc = DocumentGraph()
        >>> node1 = doc.add_node(title="Node 0", text="I'm the first node!")
        >>> print(node1)
        0
        >>> node1head, node1tail = doc.split_node(node1, 7)
        >>> [node in doc.nodes for node in (node1,node1head,node1tail)]
        [False, True, True]
        >>> print(node1head,',',node1tail)
        1 , 2
        >>> doc[node1head].text, doc[node1tail].text
        ("I'm the", ' first node!')
        >>> doc.is_dag()
        True
    """

    def __init__(self, graph=None):
        super(DocumentGraph, self).__init__()
        if graph is None:
            graph = nx.DiGraph()
        else:
            raise NotImplementedError  # Todo: remove after testing
            graph = graph
            highest_id = max(graph.node)
            update_nodecount(highest_id + 1)
        self.G = graph

    @property
    def nodes(self):
        """
        :return: frozenset containing ids for all the nodes presently defined on the graph
        :rtype: frozenset
        """
        return frozenset(self.G.nodes())

    @property
    def edges(self):
        """
        :return: (head_id,tail_id) for each of the edges on the graph
        :rtype: frozenset
        """
        return frozenset(self.G.edges())

    def __getitem__(self, key):
        if isinstance(key, int):
            nodeid = key
            nodeattribs = self.G.node[nodeid]
            try:
                return Node(nodeid=nodeid, **nodeattribs)
            except AttributeError:
                missing_attribs = ["{}, ".format(k) for k in nodeattribs if k not in Node._fields]
                raise NotImplementedError("Node namedtuple does not have fields:" + "".join(missing_attribs))
        elif isinstance(key, tuple):
            head, tail = key
            returned_edges = []
            # TODO: does this need a copy operation?
            for edge in self.G.edges(head):
                edgeattribs = self.G.edge[head][tail]
                attribs = tuple((k, v) for k, v in edgeattribs.items())
                return Edge(head=head, tail=tail, attribs=attribs)
        else:
            raise KeyError("DocumentGraph Instance Only Accepts nodeids (ints) and edgeids (tuples) as keys")

    def __setitem__(self, nodeid, valuedict):
        # TODO: Implement setitem
        raise NotImplementedError

    def __repr__(self):
        out = ["DocumentGraph("]
        edges = self.edges
        for nodeid in self.nodes:
            out.append("\t{!r}".format(self[nodeid]))
            for edge in filter(lambda x: x[0] == nodeid, edges):
                out.append("\t\t{!r}".format(self[edge]))
        out[-1] += ")"
        return "\n".join(out)

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
        # Todo: tests to check loading of yaml graphs
        G = nx.read_yaml(ymlfilepath)
        return DocumentGraph(graph=G)

    def dump_to_yaml(self, filepath=DOCGRAPHSAVELOC):
        # Todo: tests to saving of yaml graphs
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
        nodeattrs = dict(text=str(text), title=str(title))
        self.G.add_node(nodeid, nodeattrs)
        return nodeid

    def remove_node(self, nodeid):
        # Get which edges were linked to it so we can signal thier removal
        edges = list(filter(lambda edge: nodeid in edge,
                            self.G.edges()))
        self.G.remove_node(nodeid)
        # TODO: Signal the edges were removed
        # TODO: Signal the node was removed

    def add_edge(self, node1: int, node2: int):
        """
        Create an directed edge from node1 to node2.
        """
        # TODO: allow an attribute dict to be passed?
        # check that the node ids are valid for edge creation
        if not all(isinstance(node, int) for node in (node1, node2)):
            raise ValueError("add_edge only accepts integer nodeid's")
        if all(n in self.nodes for n in (node1, node2)):
            self.G.add_edge(node1, node2)
            # TODO: Potential signal point (edge instantiation on nx graph)
        else:
            raise ValueError(
                "One of ({},{}) is not in graph:\n{!r}".format(node1, node2, self))

    def remove_edge(self, head, tail):
        raise NotImplementedError

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
            (headid, tailid)
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

    def digraph_from_titles(self):
        g = nx.DiGraph()
        try:
            assert all(isinstance(nodeid, int) for nodeid in self.nodes)
        except AssertionError as e:
            print(self.nodes)
            raise e
        node_data = [self[nodeid] for nodeid in self.nodes]  # Node named tuple
        edge_data = [self[edgetuple] for edgetuple in self.edges]  # Edge named tuple
        for node in node_data:
            g.add_node(node.title)
        for edge in edge_data:
            g.add_edge(self[edge.head].title,
                       self[edge.tail].title)
        return g

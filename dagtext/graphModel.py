# from dagtext.signals import *
import itertools

import networkx as nx
from pprint import pformat
from collections import namedtuple
import signals

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


class Node(object):
    def __init__(self, nodeid, title, text):
        self.nodeid = nodeid
        self.title = title
        self.text = text

    def __str__(self):
        f = ("Node(nodeid={},title={},text={})").format(self.nodeid,
                                                        self.title,
                                                        self.text)
        return f

    def __eq__(self, other):
        try:
            if (self.title == other.title and
                        self.text == other.text and
                        self.nodeid == other.nodeid):
                return True
        except AttributeError:
            pass
        return False


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
    sig_node_created = signals.nodeCreated
    sig_node_removed = signals.nodeRemoved
    sig_node_attr_change = signals.nodeAttrChange
    sig_node_split = signals.nodeSplit
    sig_node_join = signals.nodeJoin
    sig_edge_created = signals.edgeCreated
    sig_edge_removed = signals.edgeRemoved
    sig_edge_attr_change = signals.edgeAttrChange

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
        nodeattrs = {'text': str(text), 'title': str(title)}
        self.G.add_node(nodeid, nodeattrs)
        self.sig_node_created.send(self, nodeid=nodeid)
        return nodeid

    def remove_node(self, nodeid: int):
        """
        Remove a node specified by `nodeid` from the graph.

        SIGNALS
            self.sig_node_removed.send(<docgraph>,
                                       nodeid=nodeid,
                                       nodetitle=<nodetitle>,
                                       nodetext=<nodetext>)
            self.sig_edge_removed(<docgraph>,
                                  id_tuple=(<head_node_id>,<tail_node_id>))
        RAISES
            KeyError: If the node is not in the graph
        """
        try:
            # Get information to broadcast about the node and edges being removed
            removed_edges = list(filter(lambda edge_ids: nodeid in edge_ids,
                                        self.G.edges()))
            tmpnode = self[nodeid]
            # Signal the node and edges were removed
            self.sig_node_removed.send(self,
                                       nodeid=nodeid,
                                       nodetitle=tmpnode.title,
                                       nodetext=tmpnode.text)
            for edge in removed_edges:
                self.sig_edge_removed.send(self, id_tuple=edge)

            # Do the removal
            self.G.remove_node(nodeid)
        except nx.NetworkXError:
            raise KeyError("Node %d is not in the graph" % nodeid)

    def add_edge(self, node1: int, node2: int):
        """
        Create an directed edge from node1 to node2.
        """
        # TODO: allow an attribute dict to be passed?
        # check that the node ids are valid for edge creation
        if not all(isinstance(node, int) for node in (node1, node2)):
            raise ValueError("add_edge only accepts integer nodeid's")

        # create the edge iff the nodeid's passed are currently in the graph
        nodes_on_g = self.nodes
        if all(n in nodes_on_g for n in (node1, node2)):
            self.G.add_edge(node1, node2)
            # TODO: Potential signal point (edge instantiation on nx graph)
        else:
            raise ValueError(
                "One of ({},{}) is not in graph:\n{!r}".format(node1, node2, self))

    def remove_edge(self, head, tail):
        raise NotImplementedError

    ## Checks
    def has_node(self, nodeid):
        return nodeid in self.nodes

    def has_nodes(self, *nodeids):
        nodes = self.nodes
        return all(n in nodes for n in nodeids)

    def has_edge(self, head, tail):
        return self.G.has_edge(head, tail)

    def has_edges(self, *edges):
        raise NotImplementedError

    ## Graph Rewriting/Manipulation Methods
    def split_node(self, nodeid, location,
                   in2head=True, in2tail=False,
                   head2tail=True, head2out=False,
                   tail2out=True, in2out=False):
        """
        Split a node at a given location, and connect edges as specified in the keyword arguments.

        :param nodeid: Node to be split
        :param location: Index in the node's text to split the node
        :param in2head: If True nodes w/ edges to the original node will point to the first part of the split
        :param in2tail: If True nodes w/ edges to the original node will point to the second part of the split
        :param head2tail: If True nodes the first part of the split will point to the second part of the split
        :param head2out: If True, the first part of the split will have edges to all nodes w/ edges from the original node
        :param tail2out: If True nodes w/ edges to the original node will point to the second part of the split  
        :param in2out: If True nodes w/ edges to the original node will point to all nodes w/ edges from the original node
        :type nodeid: int
        :type location: int
        :type in2head: bool
        :type in2tail: bool
        :type head2tail: bool
        :type head2out: bool
        :type tail2out: bool
        :type in2out: bool
        :returns edgeidtuple: headid, tailid
        :rtype:  (Int, Int)


            ::

                       +----+       +-----------------------+           +----+
                       |Node| ----> |        "head"         | +-------> |Node|
                       +----+       |                       |           +----+
                 +----+             | - - - location  - - - |
                 |Node| ----------> |                       |              +----+
                 +----+             |        "tail"         | +--------->  |Node|
                                    +-----------------------+              +----+


                +-------------+    +--------------------------+  +----------------+
                     "in"                  node (arg[1])               "out"

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
        self.remove_node(nodeid)
        return head, tail

    def join_nodes(self, head_node_id: int, tail_node_id: int,
                   titlesep=' + ', textsep='\n') -> int:
        """
        Join two nodes, and return new nodeid

        :param node1: id (int) of head
        :type node1:
        :param node2:
        :type node2:
        :return: created_node_id
        :rtype: int
        """
        raise NotImplementedError
        # newtitle = "[{} + {}]".format(node)
        head = self[head_node_id]
        tail = self[tail_node_id]
        # check: head -> tail

        # get: Node -> head
        # get: tail -> Node
        id_created = self.add_node(
            title=head.title + titlesep + tail.title,
            text=head.text + textsep + tail.text
        )

    def is_dag(self):
        return nx.is_directed_acyclic_graph(self.G)

    def layout(self, canvas_width, canvas_height, layout_method="spring"):
        # calculate new node positions
        width = canvas_width
        height = canvas_height

        # center of canvas
        canvas_center = (int(.5 * width), int(.5 * height))
        minreq = min(width, height)
        if layout_method == "circular":
            # TODO: add shells argument
            pos = nx.circular_layout(self.G, scale=.45 * minreq, center=canvas_center)
        elif layout_method == "spring":
            pos = nx.spring_layout(self.G, scale=.4 * minreq, center=canvas_center)
        elif layout_method == "shell":
            pos = nx.shell_layout(self.G, scale=.4 * minreq, center=canvas_center)
        elif layout_method == 'spectral':
            pos = nx.spectral_layout(self.G, scale=.4 * minreq, center=canvas_center)
        elif layout_method == 'dot':
            # For docs and summaries here: http://www.graphviz.org/doc/libguide/libguide.pdf
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog='dot', root=None)
        elif layout_method == 'neato':
            # "symmetric"? Used with undirected graphs?
            nx.drawing.nx_pydot.pydot_layout(self.G, prog='neato', root=None)
        elif layout_method == 'circo':
            # circular layout
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="circo")
        elif layout_method == 'twopi':
            # radial layout
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="twopi")
        elif layout_method == 'fdp':
            # for directed push, similar to neato
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="fdp")
        # elif layout_method == 'nop':
        #     pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="nop")
        # elif layout_method == 'nop1':
        #     pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="nop1")
        # elif layout_method == 'nop2':
        #     pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="nop2")
        elif layout_method == 'osage':
            # need's patching on pydotplus
            # clustered graphs based on user specs
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="osage")
        elif layout_method == 'patchwork':
            # may use this later (used for a treemap view)
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="patchwork")
        elif layout_method == 'sfdp':
            pos = nx.drawing.nx_pydot.pydot_layout(self.G, prog="sfdp")
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

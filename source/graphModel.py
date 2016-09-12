from signals import *
import networkx as nx
import itertools

print(SIGNALS)

class DocumentGraph(object):
    """Graph that manages nodes and edges"""

    def __init__(self):
        super(DocumentGraph, self).__init__()
        self.G = nx.DiGraph()
        self.uidcounter = itertools.count()
        self.uidLookup = {}

    def dumps(self):
        pass

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

class Node(object):
    def __init__(self, uid, text="", title=None):
        self.uid = uid
        self.text = text
        if title is None:
            self.title = "Node {}".format(self.uid)
        else:
            self.title = title

    def __repr__(self):
        return "Node(uid:{},title:{},text:{})".format(self.uid,self.title,self.text)

import tkinter as tk
import itertools
# from helpers import make_tk_image
from blinker import signal,Signal
import networkx as nx
from functools import partial


class DocumentGraph(object):
    """Graph that manages nodes and edges"""


    def __init__(self):
        super(DocumentGraph, self).__init__()
        self.G = nx.DiGraph()
        self.uidcounter = itertools.count()
        self.uidLookup = {}
        self.handleLookup = {}

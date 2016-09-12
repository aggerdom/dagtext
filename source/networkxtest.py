__author__ = 'alex'
import itertools
import networkx as nx
import tkinter as tk
# import matplotlib.pyplot as plt


class TextNode(object):
    """Base class for text node"""

    nxGraph = nx.DiGraph()
    idcounter = itertools.count()
    uid2node = {}

    def __init__(self,text=""):
        """Constructor for TextNode"""
        self.uid = next(TextNode.idcounter)
        self.text = text

        # add the node to our graph
        TextNode.nxGraph.add_node(self.uid)

        # register our node with our lookup dictionary
        TextNode.uid2node[self.uid] = self

    # ==================================================
    # Graph Handling Functions
    # ==================================================
    def add_outgoing_edge(self,targetnode):
        TextNode.nxGraph.add_edge(self.uid, targetnode.uid)

    def add_incoming_edge(self,sourcenode):
        TextNode.nxGraph.add_edge(sourcenode.uid,self.uid)

    def merge_from_incoming_node(self):
        pass

    def merge_from_outgoing_node(self):
        pass

    def split_node(self,splitindex):
        # Get the text to create one node before the split, and one after
        before = self.text[:splitindex]
        after = self.text[splitindex:]
        # TODO: Add an edge from before the after
        # TODO: Connect all the incomming edges to the before node
        # TODO: Add all the outgoing edges to exit from after node

    def is_dag(self):
        """ Check to see if we have a directed acyclic graph
        If we have an acyclic graph, it is possible to reorganize
        the nodes according to the downgraph on G """
        if nx.is_directed_acyclic_graph(TextNode.nxGraph): return True
        else: return False

    @staticmethod
    def generate_sequence_from_list_of_uids(listofuids):
        seq = []
        for uid in listofuids:
            node = TextNode.uid2node[uid]
            seq.append(node.text)
        return seq

    @staticmethod
    def flow_down_edges(startnode,endnode):
        # since nxGraph is uses node uids as keys we get a list of all simple paths, that is paths without cycles
        simplepaths = nx.all_simple_paths(TextNode.nxGraph, startnode.uid, endnode.uid) # ex: iter([[1,2,3,5],[1,2,4,5]])
        textSequences = []
        for uidlist in simplepaths:
            listofcontents = TextNode.generate_sequence_from_list_of_uids(uidlist)
            textSequences.append(listofcontents)
        return textSequences

    # ==================================================
    # Functions for tkinter
    # ==================================================
    def edit(self):
        """
        Run toplevel subroutine to edit the contents of a textnode
        """
        self.toplevel = tk.Toplevel()
        self.topFrame = tk.Frame(self.toplevel)
        self.topFrame.pack(side=tk.TOP)
        self.buttonFrame = tk.Frame(self.toplevel)
        self.buttonFrame.pack(side=tk.TOP)
        self.textWidget = tk.Text(self.topFrame)
        self.textWidget.pack()
        self.saveButton = tk.Button(self.topFrame, text="save", command = self.on_editor_save,bg="green" )
        self.saveButton.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self.exitButton = tk.Button(self.topFrame, text="exit", command = self.on_editor_exit,bg="red")
        self.exitButton.pack(side=tk.LEFT,fill=tk.X,expand=True)
        # insert contents of node into textwidget
        self.textWidget.insert(tk.END,self.text)

    def on_editor_save(self):
        """Persists the changes to the textnode since the start of the current editting session."""
        self.text = self.textWidget.get("1.0",tk.END)

    def on_editor_exit(self):
        self.toplevel.destroy()





nodes = [TextNode(text="Start")]
for n in range(10):
    nodes.append(TextNode(text="<Node {}>".format(n)))
    nodes[n].add_outgoing_edge(nodes[n+1])

nodes[0].add_outgoing_edge(nodes[-1])
uidlist = [node.uid for node in nodes]
print(uidlist)
print(TextNode.generate_sequence_from_list_of_uids(uidlist))
print(TextNode.flow_down_edges(nodes[0],nodes[-1]))
#
# for n in range(0,10):
#     nodes[n].add_outgoing_edge(nodes[n+1])
#
# pos = nx.spring_layout(TextNode.nxGraph)
# labels = {}
# for n in nodes:
#     labels[n.uid]=n.text
#
# nx.draw_networkx(TextNode.nxGraph,pos,labels=labels,font_size=16)
# plt.show()
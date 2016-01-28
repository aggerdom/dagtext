__author__ = 'alex'
import itertools
import networkx as nx
import tkinter as tk
# import matplotlib.pyplot as plt


#==============================================================================================
#
#                              TEXT NODE CLASS
#
#==============================================================================================


class TextNode(object):
    """Base class for text node"""
    nxGraph = nx.DiGraph()
    idcounter = itertools.count()
    uid2node = {}

    def __init__(self,text=""):
        """Constructor for TextNode"""
        self.uid = next(TextNode.idcounter)
        self.text = text
        self.title = self.uid

        # add the node to our graph
        TextNode.nxGraph.add_node(self.uid)

        # register our node with our lookup dictionary
        TextNode.uid2node[self.uid] = self

    # ==================================================
    # Graph Handling Functions
    # ==================================================

    def add_outgoing_edge(self,targetnode):
        """ Register an outgoing edge with the nxGraph"""
        TextNode.nxGraph.add_edge(self.uid, targetnode.uid)

    def add_incoming_edge(self,sourcenode):
        """ Register an incoming edge with the nxGraph"""
        TextNode.nxGraph.add_edge(sourcenode.uid,self.uid)

    def merge_from_incoming_node(self):
        pass

    def merge_from_outgoing_node(self):
        pass

    def split_node(self,splitindex):
        # Get the text to create one node before the split, and one after
        before = self.text[:splitindex]
        after = self.text[splitindex:]

        # TODO: Add an edge from before to the after

        # TODO: Connect all the incoming edges at the time of the split to the before node

        # TODO: Add all the outgoing edges at the time of the split to exit from after node

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

    # ====================================================================================================
    # Functions for tkinter                            
    # ====================================================================================================
    def edit(self):
        """
        Run toplevel subroutine to edit the contents of a textnode

         +-------------------------------------------------+
         | TopLevel                                        |
         +------------------------+------------------------+
         | LeftSide               | Rightside              |
         |+----------------------+|                        |
         || Title Bar            ||                        |
         |+----------------------+|                        |
         || Editor               ||                        |
         ||                      ||                        |
         ||                      ||                        |
         ||                      ||                        |
         |+----------------------+|                        |
         || Statusbar            ||                        |
         |+----------------------+|                        |
         +------------------------+------------------------|
        """
        self.toplevel = tk.Toplevel()
        
        #  ================= Get Frames for each side of the editor ===================

        self.leftSide = tk.LabelFrame(self.toplevel,text="Leftside")
        self.rightSide = tk.LabelFrame(self.toplevel,text="Rightside")
        self.leftSide.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        self.rightSide.pack(side=tk.LEFT,fill=tk.BOTH,expand=True)
        
        #  ========================== Build the leftside ===============================

        #  ===========  Frame for controlling the title of node
        self.titleFrame = tk.LabelFrame(self.leftSide,text="Title")
        self.titleFrame.pack(side=tk.TOP,fill=tk.X,expand=False)
        self.titleEntry = tk.Entry(self.titleFrame)
        self.titleEntry.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self.titleUpdateButton = tk.Button(self.titleFrame,text="Update",command=self.update_title_from_entry)
        self.titleUpdateButton.pack(side=tk.LEFT)
        
        # ============  EditorFrame
        self.editorFrame = tk.Frame(self.leftSide)
        self.editorFrame.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        self.textWidget = tk.Text(self.editorFrame)
        self.textWidget.pack(side=tk.TOP,fill=tk.BOTH,expand=True)
        
        # ============  Status Bar
        self.statusFrame = tk.LabelFrame(self.leftSide,text="Status",relief=tk.SUNKEN)
        self.statusFrame.pack(side=tk.TOP,fill=tk.X,expand=False)
        self.wordWrapStatus = tk.Menubutton(self.statusFrame)
        self.wordWrapStatus.pack()
        
        # ======================     Build the rightside ===============================
        self.buttonFrame = tk.Frame(self.rightSide)
        self.buttonFrame.pack(side=tk.TOP)
        self.saveButton = tk.Button(self.buttonFrame, text="save", command = self.on_editor_save,bg="green" )
        self.exitButton = tk.Button(self.buttonFrame, text="exit", command = self.on_editor_exit,bg="red")
        self.saveButton.pack(side=tk.LEFT,fill=tk.X,expand=True)
        self.exitButton.pack(side=tk.LEFT,fill=tk.X,expand=True)
        # insert title of node into title entry
        self.titleEntry.insert(tk.END,self.title)
        # insert contents of node into textwidget
        self.textWidget.insert(tk.END,self.text)

    def update_title_from_entry(self):
        self.title = self.titleEntry.get()

    def on_editor_save(self):
        """Persists the changes to the textnode since the start of the current editting session."""
        self.text = self.textWidget.get("1.0",tk.END)

    def on_editor_exit(self):
        self.toplevel.destroy()

#==============================================================================================
#
#                              CANVAS NODE
#
#==============================================================================================

class CanvasNode(TextNode):
    uidCounter = itertools.count()
    def __init__(self,parent,x,y,radius=15):
        """Constructor for CanvasNode"""
        super().__init__() # instantiate an empty textnode
        self.canvas = parent
        self.x,self.y = x,y
        self.radius = radius
        self.handle = self.canvas.create_oval(x,y,x+radius,y+radius)

#==============================================================================================
#
#                              CANVAS EDITOR
#
#==============================================================================================


class MyCanvas(tk.Canvas):
    def __init__(self,parent,*args,**kwargs):
        tk.Canvas.__init__(self,parent,*args,**kwargs)
        self.nodes = {} # dictionary of textnodes organized by handle
        self.bind("<1>",self.make_node)
        self.bind("<2>",self.edit_node)
        self.bind("<ButtonPress-3>",self.down)
        self.current_node = None

    def make_node(self,event):
        node = CanvasNode(self,event.x,event.y)
        # print(node.handle)
        self.nodes[node.handle]=node
        # print(self.nodes)

    def edit_node(self,event):
        itemID = self.find_closest(event.x, event.y)
        self.nodes[itemID[0]].edit()

    def down(self,event):
        """
        EVENT SEQUENCE: (part 1)
            part 1: down    - Get the node under the cursor
            part 2: motion  - update the coordinates everytime the mouse moves until button 3 is released
            part 3: up      - unbind part 2 events, and drop the node at its final location
        """
        if self.find_withtag(tk.CURRENT):
            self.current_node = self.find_withtag(tk.CURRENT)
            self.itemconfig(self.current_node,fill="blue")
            self.bind("<Motion>",self.motion)

    def motion(self,event):
        """Move the node everytime the mouse moves while the button is still down"""

        # Move nodes
        x1,y1,x2,y2 = self.coords(self.current_node)
        width, height = x2-x1, y2-y1
        newx1, newx2 = event.x - .5*width, event.x + .5*width
        newy1, newy2 = event.y - .5*height,event.y + .5*height
        self.coords(self.current_node,newx1,newy1,newx2,newy2)

        # TODO: Move start coodinates of any outgoing edges
        
        # TODO: Move the end coordinates of any incoming edges

        # Bind release events
        self.bind("<ButtonRelease-3>",self.up)

    def up(self,event):
        """Handle release of mousebutton """

        # unbind everything
        self.unbind("<Motion>")
        self.unbind("<ButtonRelease-3>")
        
        # update the coordinates at the final location (possibly unnecessary)
        x1,y1,x2,y2 = self.coords(self.current_node)
        width, height = x2-x1, y2-y1
        newx1, newx2 = event.x - .5*width, event.x + .5*width
        newy1, newy2 = event.y - .5*height,event.y + .5*height
        self.coords(self.current_node,newx1,newy1,newx2,newy2)
        self.itemconfig(self.current_node,fill="red")

if __name__ == '__main__':
    root = tk.Tk()
    frame = tk.Frame(root)
    frame.pack()
    app = MyCanvas(frame,bg="cyan")
    app.pack()
    root.mainloop()
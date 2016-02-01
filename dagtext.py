__author__ = 'alex'

import tkinter as tk
import itertools
# from helpers import make_tk_image
import networkx as nx


class Node(object):
    G = nx.DiGraph()
    uidcounter = itertools.count()
    uidLookup = {}
    handleLookup = {}

    def __init__(self, text="", title=None):
        self.uid = next(Node.uidcounter)
        self.text = text
        if title is None:
            self.title = "Node {}".format(self.uid)
        else:
            self.title = title
        # add the node to our graph structure
        Node.G.add_node(self.uid)
        # register the node with the uid 2 node lookup
        Node.uidLookup[self.uid] = self

    def instantiate(self, canvas, x, y, *args, **kwargs):
        self.x, self.y = x, y
        self.canvas = canvas
        self.handle = canvas.create_text(x, y, text=self.title, *args, **kwargs)
        self.outgoingEdgeHandles = []
        self.incomingEdgeHandles = []
        # register the node with the handle 2 node lookup
        Node.handleLookup[self.handle] = self

    # ==================================================
    # Graph Handling Functions
    # ==================================================
    def add_outgoing_edge(self, targetnode):
        Node.G.add_edge(self.uid, targetnode.uid)

    def add_incoming_edge(self, sourcenode):
        Node.G.add_edge(sourcenode.uid, self.uid)

    def merge_from_incoming_node(self):
        pass

    def merge_from_outgoing_node(self):
        pass

    def split_node(self, splitindex):
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
        if nx.is_directed_acyclic_graph(Node.G):
            return True
        else:
            return False

    @staticmethod
    def generate_sequence_from_list_of_uids(listofuids):
        seq = []
        for uid in listofuids:
            node = Node.uid2node[uid]
            seq.append(node.text)
        return seq

    @staticmethod
    def flow_down_edges(startnode, endnode):
        # since G is uses node uids as keys we get a list of all simple paths, that is paths without cycles
        simplepaths = nx.all_simple_paths(Node.G, startnode.uid, endnode.uid)  # ex: iter([[1,2,3,5],[1,2,4,5]])
        textSequences = []
        for uidlist in simplepaths:
            listofcontents = Node.generate_sequence_from_list_of_uids(uidlist)
            textSequences.append(listofcontents)
        return textSequences

    # ==================================================
    # Functions for tkinter
    # ==================================================
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
        # ============================= Frame Setup
        # Get Frames for each side of the editor
        self.leftSide = tk.LabelFrame(self.toplevel, text="Leftside")
        self.rightSide = tk.LabelFrame(self.toplevel, text="Rightside")
        self.leftSide.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.rightSide.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ####  Build the leftside
        # Frame for controlling the title of node
        self.titleFrame = tk.LabelFrame(self.leftSide, text="Title")
        self.titleFrame.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.titleEntry = tk.Entry(self.titleFrame)
        self.titleEntry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.titleUpdateButton = tk.Button(self.titleFrame, text="Update", command=self.update_title_from_entry)
        self.titleUpdateButton.pack(side=tk.LEFT)
        # ============================= EditorFrame
        self.editorFrame = tk.Frame(self.leftSide)
        self.editorFrame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.textWidget = tk.Text(self.editorFrame)
        self.textWidget.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        # ============================= Status Bar
        self.statusFrame = tk.LabelFrame(self.leftSide, text="Status", relief=tk.SUNKEN)
        self.statusFrame.pack(side=tk.TOP, fill=tk.X, expand=False)
        self.wordWrapStatus = tk.Menubutton(self.statusFrame)
        self.wordWrapStatus.pack()
        # ============================== Buttons on the right side of the editor
        self.buttonFrame = tk.Frame(self.rightSide)
        self.buttonFrame.pack(side=tk.TOP)
        self.saveButton = tk.Button(self.buttonFrame, text="save", command=self.on_editor_save, bg="green")
        self.exitButton = tk.Button(self.buttonFrame, text="exit", command=self.on_editor_exit, bg="red")
        self.saveButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.exitButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        # insert title of node into title entry
        self.titleEntry.insert(tk.END, self.title)
        # insert contents of node into textwidget
        self.textWidget.insert(tk.END, self.text)

    def update_title_from_entry(self):
        self.title = self.titleEntry.get()
        self.canvas.itemconfig(self.handle, text=self.title)

    def on_editor_save(self):
        """Persists the changes to the textnode since the start of the current editting session."""
        self.text = self.textWidget.get("1.0", tk.END)

    def on_editor_exit(self):
        self.toplevel.destroy()


# ===============================================================

class MainCanvas(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.edges = []
        self.bind("<Double-Button-1>", self.make_node)
        self.bind("<B1-Motion>", self.move_node)
        self.currentStartNode = None
        self.currentArrow = None
        self.bind("<ButtonPress-2>", self.edit_node)
        self.bind("<B3-Motion>", self.b3motion)
        self.bind("<ButtonRelease-3>", self.b3release)

    def b3motion(self, event):
        """
        If button-3 is pressed and dragged, the program will check to see if the
        click begins on a
        """
        # Selection of first node
        if self.find_withtag(tk.CURRENT) and self.currentStartNode is None:
            item = self.find_withtag(tk.CURRENT)
            self.currentStartNode = Node.handleLookup[item[0]]
        # Draw an arrow from the starting node to the current x,y
        if self.currentStartNode is not None:
            curnode = self.currentStartNode
            if self.currentArrow is None:
                self.currentArrow = self.create_line(curnode.x, curnode.y,
                                                     event.x, event.y,
                                                     arrow="last")
            else:
                newArrowCoords = curnode.x, curnode.y, event.x, event.y
                self.coords(self.currentArrow, newArrowCoords)

    def b3release(self, event):
        if self.currentArrow is not None:
            self.delete(self.currentArrow)
            self.update_idletasks()
        if self.find_withtag(tk.CURRENT):
            item = self.find_withtag(tk.CURRENT)
            if "node" in self.gettags(item):
                if self.currentStartNode is not None:
                    startingnode = self.currentStartNode
                    endingnode = Node.handleLookup[item[0]]
                    if startingnode is not endingnode:
                        # create an edge between the nodes
                        self.link_nodes(startingnode, endingnode)
                        # add update the Graph in the model to add the edge
                        startingnode.add_outgoing_edge(endingnode)
                        print("{} -> {}".format(startingnode.title,
                                                endingnode.title))
                        print(Node.G[startingnode.uid])
        self.currentStartNode = None
        self.currentArrow = None

    def make_node(self, event):
        node = Node()
        node.instantiate(self, event.x, event.y, activefill="gray", tags="node")

    def link_nodes(self, node1, node2):
        x1, y1 = self.coords(node1.handle)
        x2, y2 = self.coords(node2.handle)
        linkhandle = self.create_line(x1, y1, x2, y2, arrow='last',tags="edge")
        self.edges.append((linkhandle, node1, node2))
        node1.outgoingEdgeHandles.append(linkhandle)
        node2.incomingEdgeHandles.append(linkhandle)

    def update_edges(self):
        for edgehandle, node1, node2 in self.edges:
            self.coords(edgehandle, node1.x, node1.y, node2.x, node2.y)

    def move_node(self, event):
        if self.find_withtag(tk.CURRENT):
            item = self.find_withtag(tk.CURRENT)
            if "node" in self.gettags(item):
                # update the coordinates of the currently selected node
                node = Node.handleLookup[self.find_withtag(tk.CURRENT)[0]]
                node.x, node.y = event.x, event.y  # update x and y
                self.coords(node.handle, node.x, node.y)
                # update the coordinates for all the edges in the graph 
                # Note: Right now this is low overhead since the graphs are not large
                #       But it may be worth refactoring this to update only individual edges in the future
                self.update_edges()

    def edit_node(self, event):
        if self.find_withtag(tk.CURRENT):
            itemId = self.find_withtag(tk.CURRENT)[0]
            Node.handleLookup[itemId].edit()


# ================================================================

class Navbar(tk.LabelFrame):
    """Navigation panel on the left side of the main page"""

    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        tk.Label(self, text="this is the labelframe").pack()


# ================================================================

class Toolbar(tk.LabelFrame):
    """Ribbon at the top of the main page"""

    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.backButton = tk.Button(self, text="BACK", command=self.on_back_button)
        self.forwardButton = tk.Button(self, text="FORWARD", command=self.on_forward_button)
        self.backButton.pack(side='left', expand=False)
        self.forwardButton.pack(side='left', expand=False)

    def on_back_button(self):
        raise NotImplementedError

    def on_forward_button(self):
        raise NotImplementedError


# ================================================================

class Statusbar(tk.LabelFrame):
    """Bar at the bottom of the main page that
    displays the  current status of various aspects of the state"""

    def __init__(self, parent, *args, **kwargs):
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        tk.Label(self, text="DEMOLABEL").pack()


# ================================================================

class Main(tk.LabelFrame):
    """Body window of the main program"""

    def __init__(self, parent, *args, **kwargs):
        """Constructor for the main program window"""
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        self.canvas = MainCanvas(self, bg="orange")
        self.canvas.pack(side='top', fill='both', expand=True)


# ================================================================

class MainApplication(tk.Frame):
    """Highest level in the main program window"""

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent
        # ============== Subparts of the App Go Here
        self.statusbar = Statusbar(self, text="Statusbar")
        self.toolbar = Toolbar(self, text="Toolbar")
        self.navbar = Navbar(self, text="NavBar")
        self.main = Main(self, text="Main")

        self.statusbar.pack(side="bottom", fill="x")
        self.toolbar.pack(side="top", fill="x")
        self.navbar.pack(side="left", fill="y")
        self.main.pack(side="right", fill="both", expand=True)

        # ============== Add the menubar

        self.menubar = menubar = tk.Menu(self.parent)
        self.parent.config(menu=self.menubar)

        # Add file menu
        self.filemenu = tk.Menu(menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=self.filemenu)
        self.filemenu.add_command(label="Open", command=self.on_menu_openfile)
        self.filemenu.add_command(label="Save", command=self.on_menu_savefile)
        self.filemenu.add_separator()
        self.filemenu.add_command(label="Exit", command=self.parent.quit)

        # Add View Menu
        self.viewMenu = tk.Menu(menubar, tearoff=0)
        self.menubar.add_cascade(label="View", menu=self.viewMenu)

        # Add Edit Menu
        self.editmenu = tk.Menu(menubar, tearoff=0)
        self.editmenu.add_command(label="Cut", command=self.on_menu_cut)
        self.editmenu.add_command(label="Copy", command=self.on_menu_copy)
        self.editmenu.add_command(label="Paste", command=self.on_menu_paste)
        self.menubar.add_cascade(label="Edit", menu=self.editmenu)

        # Add Help Menu
        self.helpmenu = tk.Menu(menubar, tearoff=0)
        self.helpmenu.add_command(label="About", command=self.on_menu_about)
        self.menubar.add_cascade(label="Help", menu=self.helpmenu)

        # Bindings

    def on_left_click(self, event):
        print(event.widget)

    def on_menu_openfile(self):
        raise NotImplementedError

    def on_menu_savefile(self):
        raise NotImplementedError

    def on_menu_cut(self):
        raise NotImplementedError

    def on_menu_copy(self):
        raise NotImplementedError

    def on_menu_paste(self):
        raise NotImplementedError

    def on_menu_about(self):
        raise NotImplementedError


# ================================================================

def main():
    root = tk.Tk()
    mainapp = MainApplication(root)
    mainapp.pack(side=tk.TOP, fill="both", expand=True)
    root.mainloop()


if __name__ == '__main__':
    main()
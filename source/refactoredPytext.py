__author__ = 'alex'

import tkinter as tk
import itertools
import networkx as nx
from functools import partial
from collections import namedtuple


def intersects(a1, a2, b1, b2):
    """
    Given x,y coordinates for four points defining two lines,
    returns false if lines don't intersect
    else returns thier intersection.
    # http://stackoverflow.com/questions/3746274/line-intersection-with-aabb-rectangle
    """
    vector = namedtuple("vector", ["X", "Y"])
    a1, a2, b1, b2 = vector(*a1), vector(*a2), vector(*b1), vector(*b2)
    b = vector(a2.X - a1.X,
               a2.Y - a1.Y)
    d = vector(b2.X - b1.X,
               b2.Y - b1.Y)
    bDotDPerp = b.X * d.Y - b.Y * d.X

    # if b dot d == 0, it means the lines are parallel
    # so have infinite intersection points
    if bDotDPerp == 0:
        return False

    c = vector(b1.X - a1.X,
               b1.Y - a1.Y)
    t = (c.X * d.Y - c.Y * d.X) / bDotDPerp  # float

    if (t < 0 or t > 1):
        return False

    u = (c.X * b.Y - c.Y * b.X) / bDotDPerp  # float
    if (u < 0 or u > 1):
        return False
    intersection = vector(a1.X + t * b.X,
                          a1.Y + t * b.Y)
    return intersection


def calculateRayRectangleIntersection(pointx, pointy, rectcenterx, rectcentery, rectwidth, rectheight):
    """
          A ---------------- B
          |    rectcenter    |
          C ---------------- D
    """
    minX = rectcenterx - .5 * rectwidth
    minY = rectcentery - .5 * rectheight
    maxX = rectcenterx + .5 * rectwidth
    maxY = rectcentery + .5 * rectheight

    A = minX, minY
    B = maxX, minY
    C = minX, maxY
    D = maxX, maxY

    intAB = intersects((pointx, pointy), (rectcenterx, rectcentery), A, B)
    intAC = intersects((pointx, pointy), (rectcenterx, rectcentery), A, C)
    intBD = intersects((pointx, pointy), (rectcenterx, rectcentery), B, D)
    intCD = intersects((pointx, pointy), (rectcenterx, rectcentery), C, D)
    for possibleIntersection in (intAB, intAC, intBD, intCD):
        if possibleIntersection is not False:
            return possibleIntersection.X, possibleIntersection.Y


def color_config(widget, color, event):
    widget.configure(foreground=color)


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

        self.outgoingEdgeHandles = []
        self.incomingEdgeHandles = []

    def instantiate(self, canvas, x, y, *args, **kwargs):
        self.x, self.y = x, y
        self.canvas = canvas
        self.frame = tk.Frame(self.canvas)
        self.frame.pack()
        self.handle = canvas.create_window(x, y, window=self.frame, *args, **kwargs)

        # Construct Frame Contents
        self.toolbar = tk.LabelFrame(self.frame, relief=tk.RIDGE)
        self.toolbar.pack(side='top')
        self.dragHandle = tk.Label(self.toolbar, text="X", bg='grey')
        self.dragHandle.pack(side='left')
        self.dragHandle.bind("<ButtonPress-1>", self.draghandle_on_button_down)
        self.dragHandle.bind("<ButtonPress-3>", self.start_edge_creation)
        self.dragHandle.bind("<ButtonRelease-3>", self.end_edge_creation)

        self.titleLabel = tk.Label(self.toolbar, text=self.title)
        self.titleLabel.pack(side="top")
        self.titleLabel.bind("<Enter>", partial(color_config, self.titleLabel, "red"))
        self.titleLabel.bind("<Leave>", partial(color_config, self.titleLabel, "blue"))
        self.titleLabel.bind("<ButtonPress-1>", self.open_close_local_editor)

        self.externalEditButton = tk.Button(self.toolbar, text="[/Edit]")

        # register the node with the handle 2 node lookup
        Node.handleLookup[self.handle] = self

    def open_close_local_editor(self):
        pass

    # =================================================
    # Functions to propogate events to the underlying canvas widget
    # =================================================
    def update_Z_order(self):
        self.frame.lift()
        for edge in self.outgoingEdgeHandles:
            self.canvas.lift(edge)

    def start_edge_creation(self, event):
        # print("starting edge creation")
        self.canvas.dragEventStartNode = self
        self.canvas.event_generate("<<EdgeStartEvent>>")
        self.dragHandle.bind("<B3-Motion>", self.during_edge_creation)

    def during_edge_creation(self, event):
        self.canvas.event_generate("<<B3-Motion>>")

    def end_edge_creation(self, event):
        self.canvas.event_generate("<<EdgeRecieveEvent>>")

    def send_VirtualEVENT(self, event):
        self.canvas.currentStartNode = self.handle
        self.canvas.event_generate("<<VirtualEVENT>>")

    # def send_b3_motion(self,event):
    #     print("sending")
    #     curtags = self.canvas.gettags(self.handle)
    #     newtags = list(curtags)
    #     if tk.CURRENT not in newtags:
    #         newtags.append(tk.CURRENT)
    #     self.canvas.itemconfig(self.handle,tags=tuple(newtags))
    #     self.canvas.event_generate("<B3-Motion>")

    # ==================================================
    # Dragging of canvas window
    # ==================================================
    def draghandle_on_button_down(self, event):
        self._drag_start_coords = event.x, event.y
        self.update_Z_order()
        self.dragHandle.bind("<B1-Motion>", self.draghandle_on_button_motion)
        self.dragHandle.bind("<ButtonRelease-1>", self.draghandle_on_button_release)

    def draghandle_on_button_motion(self, event):
        """Continuously adjust the node position on the canvas"""
        curx, cury = self.canvas.coords(self.handle)
        dx = event.x - self._drag_start_coords[0]
        dy = event.y - self._drag_start_coords[1]
        newx, newy = curx + dx, cury + dy
        # update the position on the canvas
        self.canvas.coords(self.handle, newx, newy)
        # update node coordinates
        self.x = newx
        self.y = newy
        # self.canvas.update_edges()
        # self.canvas.update_edges()

    def draghandle_on_button_release(self, event):
        """Clean up after drag event"""
        self.dragHandle.unbind("<B1-Motion>")

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

    @staticmethod
    def relayout_graph(canvas, layoutMethod="spring"):
        # calculate new node positions
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        canvasCenter = list(map(int, [.5 * width, .5 * height]))  # center of canvas
        minreq = min(width, height)
        graph = Node.G
        if layoutMethod == "circular":
            pos = nx.circular_layout(graph, scale=.45 * minreq, center=canvasCenter)
        elif layoutMethod == "spring":
            pos = nx.spring_layout(graph, scale=.4 * minreq, center=canvasCenter)
        elif layoutMethod == "shell":
            pos = nx.shell_layout(graph, scale=.4 * minreq, center=canvasCenter)
        elif layoutMethod == 'spectral':
            pos = nx.spectral_layout(graph, scale=.4 * minreq, center=canvasCenter)

        # update the node positions, and move them on the canvas
        for key, position in pos.items():
            node = Node.uidLookup[key]
            node.x, node.y = position[0], position[1]
            canvas.coords(node.handle, node.x, node.y)

        # update the edge handles
        canvas.update_edges()

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
        self.dragEventStartNode = None
        self.dragEventEndNode = None
        self.currentArrow = None
        self.bind("<ButtonPress-2>", self.edit_node)
        self.bind("<B3-Motion>", self.b3motion)
        self.bind("<ButtonRelease-3>", self.b3release)
        self.bind("<<EdgeStartEvent>>", self.handle_edge_start)
        self.bind("<<EdgeRecieveEvent>>", self.handle_edge_release)

    def handle_edge_start(self, event):
        self.currentArrow = self.create_line(self.dragEventStartNode.x,
                                             self.dragEventStartNode.y,
                                             self.dragEventStartNode.x,
                                             self.dragEventStartNode.y)

    def handle_edge_release(self, event):
        if self.dragEventStartNode is not None:
            x, y = self.winfo_pointerxy()
            x = self.canvasx(x)
            y = self.canvasy(y)
            item = self.find_closest(x, y)
            if "node" in self.gettags(item):
                self.dragEventEndNode = Node.handleLookup[item[0]]
            if self.dragEventEndNode is not None:
                self.link_nodes(self.dragEventStartNode, self.dragEventEndNode)
                # add update the Graph in the model to add the edge
                self.dragEventStartNode.add_outgoing_edge(self.dragEventEndNode)
        # cleanup
        self.unbind("<B3-Motion>")
        self.dragEventStartNode = None
        self.dragEventEndNode = None

    def testvevent(self, event):
        print("IN TESTVEVENT")

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
        node.instantiate(self, event.x, event.y, tags="node")

    def link_nodes(self, node1, node2):
        x1, y1 = self.coords(node1.handle)
        x2, y2 = self.coords(node2.handle)
        linkhandle = self.create_line(x1, y1, x2, y2, arrow='last', tags="edge")
        self.edges.append((linkhandle, node1, node2))
        node1.outgoingEdgeHandles.append(linkhandle)
        node2.incomingEdgeHandles.append(linkhandle)

    def update_edges(self):
        for edgehandle, node1, node2 in self.edges:
            nodewidth = node2.frame.winfo_reqwidth()
            nodeheight = node2.frame.winfo_reqheight()
            # print(nodewidth,nodeheight)
            try:
                endx, endy = calculateRayRectangleIntersection(node1.x, node1.y, node2.x, node2.y, nodewidth,
                                                               nodeheight)
                self.coords(edgehandle, node1.x, node1.y, endx, endy)
            except TypeError:
                pass

    def move_node(self, event):
        if self.find_withtag(tk.CURRENT):
            item = self.find_withtag(tk.CURRENT)
            if "node" in self.gettags(item):
                # update the coordinates of the currently selected node
                node = Node.handleLookup[self.find_withtag(tk.CURRENT)[0]]
                node.x, node.y = event.x, event.y  # update x and y
                self.coords(node.handle, node.x, node.y)
                # update the coordinates for all the edges in the graph (Right now this is low overhead since the graphs are not large)
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
        self.parent = parent
        self.backButton = tk.Button(self, text="BACK", command=self.on_back_button)
        self.forwardButton = tk.Button(self, text="FORWARD", command=self.on_forward_button)
        self.backButton.pack(side='left', expand=False)
        self.forwardButton.pack(side='left', expand=False)
        self.layoutLabelframe = tk.LabelFrame(self, text="Layout")
        self.layoutLabelframe.pack(side='left', expand=False)
        self.springLayoutButton = tk.Button(self.layoutLabelframe, text="Spring", command=self.relayout_spring)
        self.spectralLayoutButton = tk.Button(self.layoutLabelframe, text="Spectral", command=self.relayout_spectral)
        self.circularLayoutButton = tk.Button(self.layoutLabelframe, text="Circular", command=self.relayout_circular)
        self.shellLayoutButton = tk.Button(self.layoutLabelframe, text="Shell", command=self.relayout_shell)
        self.springLayoutButton.pack(side='left', expand=False)
        self.spectralLayoutButton.pack(side='left', expand=False)
        self.circularLayoutButton.pack(side='left', expand=False)
        self.shellLayoutButton.pack(side='left', expand=False)

    def relayout_spring(self):
        Node.relayout_graph(self.parent.main.canvas, layoutMethod="spring")

    def relayout_spectral(self):
        Node.relayout_graph(self.parent.main.canvas, layoutMethod="spectral")

    def relayout_circular(self):
        Node.relayout_graph(self.parent.main.canvas, layoutMethod="circular")

    def relayout_shell(self):
        Node.relayout_graph(self.parent.main.canvas, layoutMethod="shell")

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

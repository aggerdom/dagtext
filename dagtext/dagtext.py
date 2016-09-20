__author__ = 'alex'
import tkinter as tk
import itertools


class TextNode(object):
    """Base class for text node"""

    def __init__(self, text=""):
        """Constructor for TextNode"""
        self.text = text

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
        self.textWidget.insert(tk.END, self.text)
        self.saveButton = tk.Button(self.topFrame, text="save", command=self.on_save, bg="green")
        self.saveButton.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.exitButton = tk.Button(self.topFrame, text="exit", command=self.on_exit, bg="red")
        self.exitButton.pack(side=tk.LEFT, fill=tk.X, expand=True)

    def on_save(self):
        """Persists the changes to the textnode since the start of the current editting session."""
        self.text = self.textWidget.get("1.0", tk.END)

    def on_exit(self):
        self.toplevel.destroy()


class CanvasNode(TextNode):
    uidCounter = itertools.count()

    def __init__(self, parent, x, y, radius=15):
        """Constructor for CanvasNode"""
        super().__init__()  # instantiate an empty textnode
        self.canvas = parent
        self.x, self.y = x, y
        self.radius = radius
        self.handle = self.canvas.create_oval(x, y, x + radius, y + radius)


class MyCanvas(tk.Canvas):
    def __init__(self, parent, *args, **kwargs):
        tk.Canvas.__init__(self, parent, *args, **kwargs)
        self.nodes = {}  # dictionary of textnodes organized by handle
        self.bind("<1>", self.make_node)
        self.bind("<2>", self.edit_node)
        self.bind("<ButtonPress-3>", self.down)
        self.current_node = None

    def make_node(self, event):
        node = CanvasNode(self, event.x, event.y)
        # print(node.handle)
        self.nodes[node.handle] = node
        # print(self.nodes)

    def edit_node(self, event):
        itemID = self.find_closest(event.x, event.y)
        self.nodes[itemID[0]].edit()

    def down(self, event):
        """
        EVENT SEQUENCE: (part 1)
            part 1: down    - Get the node under the cursor
            part 2: motion  - update the coordinates everytime the mouse moves until button 3 is released
            part 3: up      - unbind part 2 events, and drop the node at its final location
        """
        if self.find_withtag(tk.CURRENT):
            self.current_node = self.find_withtag(tk.CURRENT)
            self.itemconfig(self.current_node, fill="blue")
            self.bind("<Motion>", self.motion)

    def motion(self, event):
        x1, y1, x2, y2 = self.coords(self.current_node)
        width, height = x2 - x1, y2 - y1
        newx1, newx2 = event.x - .5 * width, event.x + .5 * width
        newy1, newy2 = event.y - .5 * height, event.y + .5 * height
        self.coords(self.current_node, newx1, newy1, newx2, newy2)
        self.bind("<ButtonRelease-3>", self.up)

    def up(self, event):
        # unbind everything
        self.unbind("<Motion>")
        self.unbind("<ButtonRelease-3>")
        # update the coordinates at the final location (possibly unnecessary)
        x1, y1, x2, y2 = self.coords(self.current_node)
        width, height = x2 - x1, y2 - y1
        newx1, newx2 = event.x - .5 * width, event.x + .5 * width
        newy1, newy2 = event.y - .5 * height, event.y + .5 * height
        self.coords(self.current_node, newx1, newy1, newx2, newy2)
        self.itemconfig(self.current_node, fill="red")


if __name__ == '__main__':
    root = tk.Tk()
    app = MyCanvas(root)
    app.pack()
    root.mainloop()

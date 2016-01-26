__author__ = 'alex'
import tkinter as tk
import itertools

class TextNode(object):
    """Base class for text node"""

    def __init__(self,text=""):
        """Constructor for TextNode"""
        self.text=text

    def edit(self):
        """
        Run toplevel subroutine to edit the contents of a textnode
        """
        self.toplevel = tk.Toplevel()
        self.topFrame = tk.Frame(self.toplevel)
        self.topFrame.pack()
        self.textWidget = tk.Text(self.topFrame)
        self.textWidget.pack()
        self.textWidget.insert(tk.END,self.text)
        self.saveButton = tk.Button(self.topFrame,
                                    text="save",
                                    command = self.on_save)
        self.saveButton.pack()
        self.exitButton = tk.Button(self.topFrame,
                                    text="exit",
                                    command = self.on_exit)
        self.exitButton.pack()

    def on_save(self):
        """Persists the changes to the textnode since the start of the current editting session."""
        self.text = self.textWidget.get("1.0",tk.END)

    def on_exit(self):
        self.toplevel.destroy()



class CanvasNode(TextNode):
    uidCounter = itertools.count()
    def __init__(self,parent,x,y,radius=15):
        """Constructor for CanvasNode"""
        super().__init__() # instantiate an empty textnode
        self.canvas = parent
        self.x,self.y = x,y
        self.radius = radius
        self.handle = self.canvas.create_oval(x,y,x+radius,y+radius)

class MyCanvas(tk.Canvas):
    def __init__(self,parent,*args,**kwargs):
        tk.Canvas.__init__(self,parent,*args,**kwargs)
        self.bind("<1>",self.make_node)
        self.bind("<2>",self.edit_node)
        self.nodes = {}
        self.current_node = None

    def make_node(self,event):
        node = CanvasNode(self,event.x,event.y)
        print(node.handle)
        self.nodes[node.handle]=node
        print(self.nodes)

    def demoOfCurrent(self,event):
        """Calls the edit command on the node closest to the click event"""
        #
        if self.find_withtag(tk.CURRENT):
            self.itemconfig(tk.CURRENT,fill="blue")
            self.update_idletasks()

    def edit_node(self,event):
        itemID = self.find_closest(event.x, event.y)
        self.nodes[itemID[0]].edit()

    def select_node(self,nodeId):
        # deselect and decolor current node
        if self.current_node is not None:
            self.itemconfigure(self.current_node,fill="") # clear filling
        self.current_node = nodeId
        self.itemconfigure(nodeId,fill='blue')

    def edit_test(self):
        self.textNode.edit()

if __name__ == '__main__':
    root = tk.Tk()
    app = MyCanvas(root)
    app.pack()
    root.mainloop()
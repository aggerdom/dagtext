__author__ = 'alex'
import tkinter as tk
import itertools

class TextNode(object):
    newid = itertools.count()
    def __init__(self,parent,canvas,x,y,radius=15,shape='circle',text=None):
        self.uid = next(TextNode.newid)
        self.canvas = canvas
        self.shape = shape
        self.radius = radius
        self.text = text
        self.x,self.y = x,y
        self.tag = "node{}".format(self.uid)
        if self.shape=='circle':
            self.handle = self.canvas.create_oval(x,y,x+radius,y+radius,tags=self.tag)

class Popup(tk.Menu):
    # http://stackoverflow.com/questions/15464386/how-to-pass-values-to-popup-command-on-right-click-in-python-tkinter
    def __init__(self, master,x,y,*args,**kwargs):
        tk.Menu.__init__(self, master, tearoff=0)
        self.x = x
        self.y = y
        self.add_command(label="Make Node", command=self.next)
        self.add_command(label="Edit Node")
        self.add_separator()
        self.add_command(label="Home")
    def next(self):
        print (self.x, self.y)




class App(tk.Frame):
    def __init__(self,parent):
        tk.Frame.__init__(self,parent)
        self.parent = parent
        self.canv = tk.Canvas(self,width=850,height=400)
        self.canv.pack()
        self.canv.bind("<1>",self.make_node)
        # handle right click events
        self.canv.bind("<Button-3>",self.do_popup_event)

    def do_popup_event(self,event):
        popup = Popup(self, event.x, event.y)
        try:
            popup.tk_popup(event.x_root, event.y_root)
        finally:
            popup.grab_release()


    def make_node(self,event):
        node = TextNode(self,self.canv,event.x,event.y)
        #self.canv.tag_bind(node.tag,"<3>",self.on_object_click)

    def on_object_click(self,event):
        print(event.widget.find_closest(event.x, event.y))

    def select_node(self,event):
        item = self.canv.find_closest(event.x, event.y)



if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    app.pack(fill=tk.BOTH, expand=tk.YES)
    root.mainloop()
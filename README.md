# Dagtext - An experimental non-linear texteditor

This repo will come to hold an experimental text editor, currently a work in progress.

![Snapshot of Development Version of Dagtext](http://i.imgur.com/uNBo0CK.png)


## ROADMAP

1. [x] Create the textnode base class, and the toplevel editor subroutine
2. [x] Allow the user to click to place nodes
3. [x] Allow the user to click to edit nodes
4. [x] Add the ability to drag and drop nodes
5. [ ] Add the logic for merging and splitting nodes
6. [x] Get the edges to update when the nodes move positions
7. [ ] Add the ability to merge nodes
8. [ ] Add the ability to split nodes
9. [x] Add the logic to encode edges
10. [x] Add the code to connect nodes with edges
11. [ ] Add the ability to specify a starting node and have text cascade down edges
12. [ ] Add the ability to navigate between node editing sessions
13. [ ] Add the ability to create nodes out of flatfiles
14. [ ] File dialog logic

## Tutorial

Welcome to dagText! Upon running dagtext, you will be presented with a orange canvas representing what is known as a directed graph or DiGraph.

### Canvas Controls

- Double click to add nodes to the graph
- Left click and drag a node to move it around the canvas
- Right click on a node, and release the button on top of another node to link them with an edge
- Middle click on a node to edit the text contents of the node or to change the title of the node

#### Technical Specification

Graph operations are handled within the Node class. When a node is created on the canvas, a unique id is assigned to the the node, and that uid is added to `Node.uidLookup` for ease of reference as well as to `Node.G` for use in Graph Theoretic Operations. Each node carries with it a title (for use identifying the node in the canvas editor) and has text contents accessible via <Node>.text (more on this later). 

When edges are added on the canvas, we take note of which nodes A and B start and end the edge, and add (1) an edge A.uid -> B.uid on Node.G, and (2) a tuple (edgehandle, A, B) to MainCanvas.edges which is used for updating the position of edges as nodes are repositioned. 


To persist a project (not yet implemented):

1. create a directory
2. create a file for each document named with the title of nodes (will require making these unique...)
3. create config file mapping filenames to uids, as well as x and y coordinates.

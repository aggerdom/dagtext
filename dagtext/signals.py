from blinker import signal
SIGNALS = {
    "nodeCreated"    : signal("nodeCreated"),
    "nodeRemoved"    : signal("nodeDestroyed"),
    "nodeSplit"      : signal("nodeSplit"),
    "nodeJoin"       : signal("nodeJoin"),
    "edgeRemoved"    : signal("edgeRemoved"),
    "edgeCreated"    : signal("edgeRemoved"),
    "graphRelayout"  : signal("graphRelayout"),
    "requestCanvases": signal("requestCanvases"),
}

# save event
save = signal("save")

# Alterations on the graph
nodeCreated = signal("nodeCreated")
nodeRemoved = signal("nodeDestroyed")
nodeSplit = signal("nodeSplit")
nodeJoin = signal("nodeJoin")
edgeCreated = signal("edgeRemoved")
edgeRemoved = signal("edgeRemoved")
edgeAttrChange = signal("edgeAttrChange")

# Alterations on the gui
graphRelayout = signal("graphRelayout")
requestCanvases = signal("requestCanvases")

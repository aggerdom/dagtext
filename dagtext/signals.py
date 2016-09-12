from blinker import signal
SIGNALS = {
    "nodeCreated": signal("nodeCreated"),
    "nodeDestroyed": signal("nodeDestroyed"),
    "nodeSplit": signal("nodeSplit"),
    "nodeJoin": signal("nodeJoin"),
    "graphRelayout": signal("graphRelayout"),
    "requestCanvases": signal("requestCanvases"),
}
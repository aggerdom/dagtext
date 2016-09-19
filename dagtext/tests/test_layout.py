import pydotplus
import networkx
import matplotlib.pyplot as plt

g = networkx.DiGraph()  # type: nx.DiGraph
nodes = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
labels = {l: l for l in nodes}
g.add_path(('a', 'b', 'c', 'd'))
g.add_path(('e', 'f', 'g'))
g.add_path(('e', 'h'))

# nx.draw(g,labels=labels)
# plt.show()

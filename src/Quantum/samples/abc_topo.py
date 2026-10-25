from sequence.topology.qkd_topo import QKDTopo

topo = QKDTopo("abc_topo.json")

nodes = topo.get_nodes_by_type("QKDNode")
print("Nodes created:", [n.name for n in nodes])

print("Timeline stop time:", topo.tl.stop_time)

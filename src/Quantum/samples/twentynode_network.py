from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel

# 1. Initialize Timeline
tl = Timeline()

# 2. Configuration Parameters
num_nodes = 20
distance_between_nodes = 1000  # 1km
attenuation = 0.0002

nodes = []

# 3. Create Nodes in a Loop
for i in range(num_nodes):
    node_name = f"Node_{i}"
    new_node = Node(node_name, tl)
    nodes.append(new_node)

# 4. Connect Nodes in a Line Topology
# We loop until num_nodes - 1 to connect Node_i to Node_i+1
for i in range(num_nodes - 1):
    src = nodes[i]
    dest = nodes[i+1]
    
    # Create Quantum Channel (Node_i -> Node_i+1)
    qc_name = f"QC_{src.name}_{dest.name}"
    qc = QuantumChannel(qc_name, tl, attenuation=attenuation, 
                        distance=distance_between_nodes, polarization_fidelity=0.99)
    qc.set_ends(src, dest.name)
    
    # Create Classical Channel (Node_i <-> Node_i+1)
    # Required for almost all quantum protocols like BB84 or Entanglement Swapping
    cc_name = f"CC_{src.name}_{dest.name}"
    cc = ClassicalChannel(cc_name, tl, distance=distance_between_nodes)
    cc.set_ends(src, dest.name)

# 5. Initialize and Run
tl.init()
tl.run()

print(f"Successfully created a quantum network with {len(nodes)} nodes.")
print(f"Total network distance: {(num_nodes-1) * distance_between_nodes / 1000} km")

print("List of nodes in the network:")
for node in nodes:
    print(f" - {node.name}")
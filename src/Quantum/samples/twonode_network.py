from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node
from sequence.components.optical_channel import QuantumChannel

# 1. Timeline
tl = Timeline()

# 2. Nodes
alice = Node("Alice", tl)
bob = Node("Bob", tl)

# 3. Quantum Channel for Alice and Bob (Bidirectional)
qc = QuantumChannel("QC_AB", tl, attenuation=0.0002, distance=1000, polarization_fidelity=0.99)

# 4. Connect Channels
qc.set_ends(alice, bob.name)

# 5. Initialize and run
tl.init()
tl.run()

print("Quantum network created!")
print("Timeline:", tl)





# ✅ Two nodes connected by ONE quantum channel
# ✅ Infrastructure ready for quantum operations
# ✅ Bidirectional communication enabled
# ❌ But no quantum hardware yet (can't actually store/send qubits)

# THEY COULD:
# ✅ Send/receive photons
# ✅ Forward signals

# THEY COULD NOT:
# ❌ Store quantum states
# ❌ Generate entanglement
# ❌ Participate in protocols
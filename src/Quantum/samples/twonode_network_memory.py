from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node
from sequence.components.optical_channel import QuantumChannel
from sequence.components.memory import Memory

# 1. Timeline
tl = Timeline()

# 2. Nodes
alice = Node("Alice", tl)
bob = Node("Bob", tl)

# 3. Add Quantum Memories
alice_mem = Memory("Alice_Memory", tl, fidelity=0.95, frequency=2000, efficiency=0.85, coherence_time=1e11, wavelength=1550)
bob_mem = Memory("Bob_Memory", tl, fidelity=0.95, frequency=2000, efficiency=0.85, coherence_time=1e11, wavelength=1550)

alice.add_component(alice_mem)
bob.add_component(bob_mem)

# 3. Quantum Channel for Alice and Bob (Bidirectional)
qc = QuantumChannel("QC_AB", tl, attenuation=0.0002, distance=1000, polarization_fidelity=0.99)

# 4. Connect Channels
qc.set_ends(alice, bob.name)

# 5. Initialize and run
tl.init()
tl.run()

print("Quantum network created!")
print(f"{alice.name} <--quantum--> {bob.name}")
print("Timeline:", tl.now())



# YOUR NODES ARE NOW:
# ✅ Quantum-capable nodes

# THEY CAN:
# ✅ Store qubits
# ✅ Participate in entanglement generation
# ✅ Support teleportation, QKD, repeaters
# ✅ Run memory-based protocols
# ✅ This is the minimum requirement for real quantum networks.

# THEY CAN NOT:
# ❌ Still no events are scheduled
# ❌ But they are empty
# ❌ No entanglement generated
# ❌ No measurements
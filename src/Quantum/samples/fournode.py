import time
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import BB84, pair_bb84_protocols

class TrustedRelay:
    def __init__(self, name):
        self.name = name
        self.links = {}   # peer_name -> QKDNode

    def add_link(self, peer, node):
        self.links[peer] = node

    def get_key(self, peer):
        return self.links[peer].protocol_stack[0].key


def run_topology(sim_time_ms=20, keysize=256):

    # 1. Timeline
    tl = Timeline(sim_time_ms * 1e9)

    # 2. Create nodes
    A = QKDNode("A", tl, stack_size=1)

    # B is split into 3 physical QKD interfaces
    B_AB = QKDNode("B_AB", tl, stack_size=1)
    B_BC = QKDNode("B_BC", tl, stack_size=1)
    B_BD = QKDNode("B_BD", tl, stack_size=1)

    # Logical trusted relay B
    B = TrustedRelay("B")
    B.add_link("A", B_AB)
    B.add_link("C", B_BC)
    B.add_link("D", B_BD)

    C = QKDNode("C", tl, stack_size=1)
    D = QKDNode("D", tl, stack_size=1)

    # Seeds
    A.set_seed(0)
    B_AB.set_seed(1)
    B_BC.set_seed(2)
    B_BD.set_seed(3)
    C.set_seed(4)
    D.set_seed(5)

    # 3. Pair BB84 protocols (one per physical link)
    pair_bb84_protocols(A.protocol_stack[0], B_AB.protocol_stack[0])   # A–B
    pair_bb84_protocols(B_BC.protocol_stack[0], C.protocol_stack[0])   # B–C
    pair_bb84_protocols(B_BD.protocol_stack[0], D.protocol_stack[0])   # B–D

    # --------------------------------------------------
    # 4. Channels
    # --------------------------------------------------

    def connect(n1, n2, label):
        QuantumChannel(f"qc_{label}_1", tl, distance=1e6, attenuation=1e-5, polarization_fidelity=1).set_ends(n1, n2.name)
        QuantumChannel(f"qc_{label}_2", tl, distance=1e6, attenuation=1e-5, polarization_fidelity=1).set_ends(n2, n1.name)
        ClassicalChannel(f"cc_{label}_1", tl, distance=1e3).set_ends(n1, n2.name)
        ClassicalChannel(f"cc_{label}_2", tl, distance=1e3).set_ends(n2, n1.name)
               

    connect(A, B_AB, "AB")
    connect(B_BC, C, "BC")
    connect(B_BD, D, "BD")

    # 5. Initialize simulation
    tl.init()

    # 6. Request one key per link
    A.protocol_stack[0].push(keysize, 1)
    B_BC.protocol_stack[0].push(keysize, 1)
    B_BD.protocol_stack[0].push(keysize, 1)

    print("Running 4-node topology simulation...")
    start = time.time()
    tl.run()
    print("Finished in %.2f sec\n" % (time.time() - start))

    # --------------------------------------------------
    # 7. Verification
    # --------------------------------------------------

    print("=== PRINT KEY ===")
    print("== A-B ==")
    print("A key: ", A.protocol_stack[0].key)
    print("A key: ", B_AB.protocol_stack[0].key)

    print("== B-C ==")
    print("B key: ", B_BC.protocol_stack[0].key)
    print("B key: ", C.protocol_stack[0].key)

    print("== B-D ==")
    print("B key: ", B_BD.protocol_stack[0].key)
    print("B key: ", D.protocol_stack[0].key)


    print("\n=== KEY VERIFICATION ===")
    print("A–B match:",
          A.protocol_stack[0].key == B_AB.protocol_stack[0].key)
    print("B–C match:",
          B_BC.protocol_stack[0].key == C.protocol_stack[0].key)
    print("B–D match:",
          B_BD.protocol_stack[0].key == D.protocol_stack[0].key)
    

    print("\n=== KEY LENGTHS ===")
    print("A–B:", A.protocol_stack[0].key.bit_length())
    print("B–C:", B_BC.protocol_stack[0].key.bit_length())
    print("B–D:", B_BD.protocol_stack[0].key.bit_length())


# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    run_topology()
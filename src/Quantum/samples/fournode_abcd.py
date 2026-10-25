# No photon detection

import time
import math

from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols, BB84
from sequence.qkd.cascade import Cascade
from sequence.kernel.event import Event
from sequence.kernel.process import Process


def xor_encrypt(msg_bytes: bytes, key_int: int) -> bytes:
    if key_int is None:
        raise ValueError("Key is None.")
    key_bytes = key_int.to_bytes((key_int.bit_length() + 7) // 8, "big")
    if len(key_bytes) == 0:
        raise ValueError("Key has 0 bits.")
    full_key = (key_bytes * ((len(msg_bytes) // len(key_bytes)) + 1))[:len(msg_bytes)]
    return bytes([m ^ k for m, k in zip(msg_bytes, full_key)])


def connect(tl, n1, n2, label, distance=1000, attenuation=0.0002, pol_fid=1):
    QuantumChannel(
        f"qc_{label}_1", tl,
        distance=distance,
        attenuation=attenuation,
        polarization_fidelity=pol_fid
    ).set_ends(n1, n2.name)

    QuantumChannel(
        f"qc_{label}_2", tl,
        distance=distance,
        attenuation=attenuation,
        polarization_fidelity=pol_fid
    ).set_ends(n2, n1.name)

    ClassicalChannel(f"cc_{label}_1", tl, distance=distance).set_ends(n1, n2.name)
    ClassicalChannel(f"cc_{label}_2", tl, distance=distance).set_ends(n2, n1.name)



# Attach BB84 + Cascade dynamically to a node created with stack_size=0
def attach_bb84_stack2(node: QKDNode):
    if node.protocol_stack[0] is not None:
        return node.protocol_stack[0]

    ls_name = f"{node.name}.lightsource"
    det_name = f"{node.name}.qsdetector"

    bb84 = BB84(node, f"{node.name}.BB84", ls_name, det_name)
    cascade = Cascade(node, f"{node.name}.cascade")

    node.protocol_stack[0] = bb84
    node.protocol_stack[1] = cascade
    node.protocols.append(bb84)
    node.protocols.append(cascade)

    bb84.upper_protocols.append(cascade)
    cascade.lower_protocols.append(bb84)

    return bb84


def run(destination="C", keysize=256, runtime_ms=200):
    assert destination in ("C", "D")

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = True


    # A and B - BB84
    A = QKDNode("A", tl, stack_size=2)  
    B = QKDNode("B", tl, stack_size=2)

    C = QKDNode("C", tl, stack_size=0)
    D = QKDNode("D", tl, stack_size=0)

    # Channels
    connect(tl, A, B, "AB")
    connect(tl, B, C, "BC")
    connect(tl, B, D, "BD")

    bb84_A = A.protocol_stack[0]
    bb84_B = B.protocol_stack[0]

    pair_bb84_protocols(bb84_A, bb84_B)
    store = {"K_AB_A": None, "K_AB_B": None, "K_BX_B": None, "K_BX_X": None}

 
    class Runner:
        def __init__(self, fn): self.fn = fn
        def run(self): self.fn()

    # A-B
    def start_AB():
        bb84_A.push(keysize, 1)

    def capture_AB():
        store["K_AB_A"] = bb84_A.key
        store["K_AB_B"] = bb84_B.key
        print("\n[CAPTURE] AB keys:")
        print("A key:", store["K_AB_A"])
        print("B key:", store["K_AB_B"])

    # B -> dest
    def start_BX():
        dest_node = C if destination == "C" else D
        bb84_X = attach_bb84_stack2(dest_node)
        pair_bb84_protocols(bb84_B, bb84_X)
        bb84_B.push(keysize, 1)

    def capture_BX():
        dest_node = C if destination == "C" else D
        bb84_X = dest_node.protocol_stack[0]
        store["K_BX_B"] = bb84_B.key
        store["K_BX_X"] = bb84_X.key
        print(f"\n[CAPTURE] B-{destination} keys:")
        print("B key:", store["K_BX_B"])
        print(f"{destination} key:", store["K_BX_X"])

    # schedule phases
    tl.schedule(Event(0, Process(Runner(start_AB), "run", [])))
    tl.schedule(Event(int(30e9), Process(Runner(capture_AB), "run", [])))

    tl.schedule(Event(int(60e9), Process(Runner(start_BX), "run", [])))
    tl.schedule(Event(int(90e9), Process(Runner(capture_BX), "run", [])))

    # run simulation
    print(f"\n=== RUN: A -> {destination} via B (trusted relay) ===")
    start = time.time()
    tl.init()
    tl.run()
    print("Finished in %.2f sec" % (time.time() - start))

    # validate + relay
    K_AB_A, K_AB_B = store["K_AB_A"], store["K_AB_B"]
    K_BX_B, K_BX_X = store["K_BX_B"], store["K_BX_X"]

    ok_ab = (K_AB_A is not None and K_AB_A == K_AB_B)
    ok_bx = (K_BX_B is not None and K_BX_B == K_BX_X)

    print("\n=== LINK STATUS ===")
    print("AB established:", ok_ab)
    print(f"B-{destination} established:", ok_bx)

    if not (ok_ab and ok_bx):
        print("Relay skipped: link keys not correct.")
        return

    # Trusted relay demo message A -> destination via B
    msg = b"HELLO C" if destination == "C" else b"HELLO D"
    cipher1 = xor_encrypt(msg, K_AB_A)     # using AB key
    plainB  = xor_encrypt(cipher1, K_AB_B) # B decrypt
    cipher2 = xor_encrypt(plainB, K_BX_B)  # B-dest
    plainX  = xor_encrypt(cipher2, K_BX_X) # destination decrypt

    print("\n=== TRUSTED RELAY ===")
    print("Original:", msg)
    print("Delivered:", plainX)
    print("Correct:", plainX == msg)


if __name__ == "__main__":
    run(destination="C")  


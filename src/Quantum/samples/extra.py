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


def connect(tl, n1, n2, label, distance=1000, attenuation=0.0002, pol_fid=0.99):
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


def enable_bb84_metrics(bb84: BB84):
    if hasattr(bb84, "photons_sent"):
        return 

    bb84.photons_sent = 0
    bb84.photons_received = 0

    orig_begin = bb84.begin_photon_pulse
    orig_end = bb84.end_photon_pulse

    def begin_wrapper():
        num_pulses = round(bb84.light_time * bb84.ls_freq)
        bb84.photons_sent += num_pulses
        orig_begin()

    def end_wrapper():
        orig_end()
        if bb84.bit_lists and len(bb84.bit_lists) > 0:
            last_bits = bb84.bit_lists[-1]
            bb84.photons_received += sum(1 for b in last_bits if b != -1)

    bb84.begin_photon_pulse = begin_wrapper
    bb84.end_photon_pulse = end_wrapper


def run(path="C", keysize=256, runtime_ms=300):
    """
    path: "C" means A→B→C→F, "D" means A→B→D→F
    """
    assert path in ("C", "D")

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = True

    # Create nodes
    A = QKDNode("A", tl, stack_size=2)
    B = QKDNode("B", tl, stack_size=2)
    C = QKDNode("C", tl, stack_size=2)
    D = QKDNode("D", tl, stack_size=2)
    F = QKDNode("F", tl, stack_size=2)  # Final destination

    # Build topology: A-B-C-F and A-B-D-F
    connect(tl, A, B, "AB", distance=30000)
    connect(tl, B, C, "BC", distance=40000)
    connect(tl, B, D, "BD", distance=40000)
    connect(tl, C, F, "CF", distance=35000)
    connect(tl, D, F, "DF", distance=35000)

    bb84_A = A.protocol_stack[0]
    bb84_B = B.protocol_stack[0]

    enable_bb84_metrics(bb84_A)
    enable_bb84_metrics(bb84_B)

    pair_bb84_protocols(bb84_A, bb84_B)

    # Storage for all keys in the path
    store = {
        "K_AB_A": None, "K_AB_B": None,
        "K_BX_B": None, "K_BX_X": None,
        "K_XF_X": None, "K_XF_F": None
    }

    class Runner:
        def __init__(self, fn): 
            self.fn = fn
        def run(self): 
            self.fn()

    # ============ PHASE 1: A-B ============
    def start_AB():
        bb84_A.photons_sent = 0
        bb84_B.photons_received = 0
        bb84_A.error_rates = []
        bb84_B.error_rates = []
        bb84_A.push(keysize, 1)

    def capture_AB():
        store["K_AB_A"] = bb84_A.key
        store["K_AB_B"] = bb84_B.key

        print("\n[PHASE 1] A-B key establishment")
        print("A key:", store["K_AB_A"])
        print("B key:", store["K_AB_B"])
        print("Photons sent (A):", bb84_A.photons_sent)
        print("Photons received (B):", bb84_B.photons_received)
        qber = bb84_A.error_rates[-1] if bb84_A.error_rates else None
        print("QBER (A-B):", qber)

    # ============ PHASE 2: B-C or B-D ============
    def start_BX():
        intermediate = C if path == "C" else D
        bb84_X = attach_bb84_stack2(intermediate)
        enable_bb84_metrics(bb84_X)

        bb84_B.photons_sent = 0
        bb84_X.photons_received = 0
        bb84_B.error_rates = []
        bb84_X.error_rates = []

        pair_bb84_protocols(bb84_B, bb84_X)
        bb84_B.push(keysize, 1)

    def capture_BX():
        intermediate = C if path == "C" else D
        bb84_X = intermediate.protocol_stack[0]

        store["K_BX_B"] = bb84_B.key
        store["K_BX_X"] = bb84_X.key

        print(f"\n[PHASE 2] B-{path} key establishment")
        print("B key:", store["K_BX_B"])
        print(f"{path} key:", store["K_BX_X"])
        print("Photons sent (B):", bb84_B.photons_sent)
        print(f"Photons received ({path}):", bb84_X.photons_received)
        qber = bb84_B.error_rates[-1] if bb84_B.error_rates else None
        print(f"QBER (B-{path}):", qber)

    # ============ PHASE 3: C/D-F ============
    def start_XF():
        intermediate = C if path == "C" else D
        bb84_X = intermediate.protocol_stack[0]
        bb84_F = attach_bb84_stack2(F)
        enable_bb84_metrics(bb84_F)

        bb84_X.photons_sent = 0
        bb84_F.photons_received = 0
        bb84_X.error_rates = []
        bb84_F.error_rates = []

        pair_bb84_protocols(bb84_X, bb84_F)
        bb84_X.push(keysize, 1)

    def capture_XF():
        intermediate = C if path == "C" else D
        bb84_X = intermediate.protocol_stack[0]
        bb84_F = F.protocol_stack[0]

        store["K_XF_X"] = bb84_X.key
        store["K_XF_F"] = bb84_F.key

        print(f"\n[PHASE 3] {path}-F key establishment")
        print(f"{path} key:", store["K_XF_X"])
        print("F key:", store["K_XF_F"])
        print(f"Photons sent ({path}):", bb84_X.photons_sent)
        print("Photons received (F):", bb84_F.photons_received)
        qber = bb84_X.error_rates[-1] if bb84_X.error_rates else None
        print(f"QBER ({path}-F):", qber)

    # Schedule all phases
    tl.schedule(Event(0,           Process(Runner(start_AB), "run", [])))
    tl.schedule(Event(int(40e9),   Process(Runner(capture_AB), "run", [])))

    tl.schedule(Event(int(60e9),   Process(Runner(start_BX), "run", [])))
    tl.schedule(Event(int(100e9),  Process(Runner(capture_BX), "run", [])))

    tl.schedule(Event(int(120e9),  Process(Runner(start_XF), "run", [])))
    tl.schedule(Event(int(160e9),  Process(Runner(capture_XF), "run", [])))

    print(f"\n=== SIMULATION: A → B → {path} → F (3-hop trusted relay) ===")
    start = time.time()
    tl.init()
    tl.run()
    print("Finished in %.2f sec" % (time.time() - start))

    # ============ VALIDATE & RELAY ============
    K_AB_A = store["K_AB_A"]
    K_AB_B = store["K_AB_B"]
    K_BX_B = store["K_BX_B"]
    K_BX_X = store["K_BX_X"]
    K_XF_X = store["K_XF_X"]
    K_XF_F = store["K_XF_F"]

    ok_ab = (K_AB_A is not None and K_AB_A == K_AB_B)
    ok_bx = (K_BX_B is not None and K_BX_B == K_BX_X)
    ok_xf = (K_XF_X is not None and K_XF_X == K_XF_F)

    print("\n=== LINK STATUS ===")
    print("A-B established:", ok_ab)
    print(f"B-{path} established:", ok_bx)
    print(f"{path}-F established:", ok_xf)

    if not (ok_ab and ok_bx and ok_xf):
        print("❌ Relay failed: not all keys established correctly.")
        return

    # 3-hop trusted relay: A → B → C/D → F
    msg = b"HELLO F VIA PATH " + path.encode()
    
    cipher1 = xor_encrypt(msg, K_AB_A)         # A encrypts
    plainB = xor_encrypt(cipher1, K_AB_B)      # B decrypts
    
    cipher2 = xor_encrypt(plainB, K_BX_B)      # B re-encrypts
    plainX = xor_encrypt(cipher2, K_BX_X)      # C/D decrypts
    
    cipher3 = xor_encrypt(plainX, K_XF_X)      # C/D re-encrypts
    plainF = xor_encrypt(cipher3, K_XF_F)      # F decrypts

    print("\n=== 3-HOP TRUSTED RELAY ===")
    print("Original message:", msg)
    print("Delivered to F  :", plainF)
    print("✓ Correct delivery:", plainF == msg)


if __name__ == "__main__":
    run(path="C")  # Try path="D" for A→B→D→F
import time
import random

from sequence.components.photon import Photon
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import BB84, pair_bb84_protocols
from sequence.qkd.cascade import Cascade, pair_cascade_protocols
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


def connect(tl, n1, n2, label, distance=1000, attenuation=0.0002, pol_fid=0.95):
    QuantumChannel(f"qc_{label}_1", tl, distance=distance, attenuation=attenuation,
                   polarization_fidelity=pol_fid).set_ends(n1, n2.name)
    QuantumChannel(f"qc_{label}_2", tl, distance=distance, attenuation=attenuation,
                   polarization_fidelity=pol_fid).set_ends(n2, n1.name)
    ClassicalChannel(f"cc_{label}_1", tl, distance=distance).set_ends(n1, n2.name)
    ClassicalChannel(f"cc_{label}_2", tl, distance=distance).set_ends(n2, n1.name)


def attach_bb84_cascade_stack(node: QKDNode, role: int = -1):
    if len(node.protocol_stack) >= 2 and node.protocol_stack[0] is not None:
        return node.protocol_stack[0], node.protocol_stack[1]

    if len(node.protocol_stack) < 2:
        node.protocol_stack = [None, None]

    ls_name = f"{node.name}.lightsource"
    det_name = f"{node.name}.qsdetector"

    bb84 = BB84(node, f"{node.name}.BB84", ls_name, det_name)
    cascade = Cascade(node, f"{node.name}.cascade", role=role)

    node.protocol_stack[0] = bb84
    node.protocol_stack[1] = cascade
    node.protocols.append(bb84)
    node.protocols.append(cascade)

    bb84.upper_protocols.append(cascade)
    cascade.lower_protocols.append(bb84)

    return bb84, cascade


def reset_node_protocols(node: QKDNode):
    node.protocol_stack = [None, None]
    node.protocols = []


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


def reset_metrics(bb84_sender: BB84, bb84_receiver: BB84):
    bb84_sender.photons_sent = 0
    bb84_receiver.photons_received = 0


class InterceptResend:
    def __init__(self, p_attack=1.0):
        self.enabled = True
        self.p_attack = p_attack
        self.attacked = 0
        self.forwarded = 0

    def intercept(self, photon: Photon) -> Photon:
        self.forwarded += 1
        if (not self.enabled) or (random.random() > self.p_attack):
            return photon
        self.attacked += 1
        new_photon = Photon(
            name=f"Eve_{self.attacked}",
            timeline=photon.timeline,
            wavelength=photon.wavelength,
            location="Eve",
            encoding_type=photon.encoding_type
        )
        return new_photon

def get_cascade_key(cascade, keysize):
    """Extract a single key of correct size from Cascade valid_keys."""
    if cascade.valid_keys:
        key = cascade.valid_keys[0] & ((1 << keysize) - 1)
        return key
    return None


def run(route="C", keysize=128, runtime_ms=500):
    assert route in ("C", "D")

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = True

    A = QKDNode("A", tl, stack_size=0)
    B = QKDNode("B", tl, stack_size=0)
    C = QKDNode("C", tl, stack_size=0)
    D = QKDNode("D", tl, stack_size=0)
    F = QKDNode("F", tl, stack_size=0)

    connect(tl, A, B, "AB")
    connect(tl, B, C, "BC")
    connect(tl, B, D, "BD")
    connect(tl, C, F, "CF")
    connect(tl, D, F, "DF")

    eve = InterceptResend(p_attack=0.5)
    qc_AB = A.qchannels["B"]
    orig_transmit = qc_AB.transmit

    def eve_transmit(photon, *args, **kwargs):
        photon2 = eve.intercept(photon)
        return orig_transmit(photon2, *args, **kwargs)

    qc_AB.transmit = eve_transmit
    eve.enabled = False

    protocols = {}
    store = {}

    class Runner:
        def __init__(self, fn):
            self.fn = fn
        def run(self):
            self.fn()

    # A <-> B
    def start_AB():
        bb84_A, cascade_A = attach_bb84_cascade_stack(A, role=0)
        bb84_B, cascade_B = attach_bb84_cascade_stack(B, role=1)
        pair_bb84_protocols(bb84_A, bb84_B)
        pair_cascade_protocols(cascade_A, cascade_B)
        enable_bb84_metrics(bb84_A)
        enable_bb84_metrics(bb84_B)
        reset_metrics(bb84_A, bb84_B)
        protocols["AB"] = {"A": (bb84_A, cascade_A), "B": (bb84_B, cascade_B)}
        cascade_A.push(keysize, frame_num=1, run_time=int(40e9))

    def capture_AB():
        bb84_A, cascade_A = protocols["AB"]["A"]
        bb84_B, cascade_B = protocols["AB"]["B"]

        # BB84 keys
        print("\n[CAPTURE] AB keys:")
        print("A BB84 key:", bb84_A.key)
        print("B BB84 key:", bb84_B.key)

        # Cascade corrected keys
        cascade_key_A = get_cascade_key(cascade_A, keysize)
        cascade_key_B = get_cascade_key(cascade_B, keysize)
        print("\nA Cascade key:", cascade_key_A)
        print("B Cascade key:", cascade_key_B)

        store["K_AB_A"] = cascade_key_A
        store["K_AB_B"] = cascade_key_B

        print("\n[METRICS] A -> B")
        print("Photons emitted at A:", bb84_A.photons_sent)
        print("Photons captured at B:", bb84_B.photons_received)
        qber = bb84_A.error_rates[-1] if hasattr(bb84_A, 'error_rates') and bb84_A.error_rates else None
        print("QBER (AB):", qber)

        print("\n[EVE STATS]")
        print("Intercepted:", eve.attacked)
        print("Forwarded:", eve.forwarded)
        if eve.forwarded > 0:
            print("% attack:", (eve.attacked * 100 / eve.forwarded))

    # B <-> X
    def start_BX():
        X = C if route == "C" else D
        reset_node_protocols(B)
        bb84_B, cascade_B = attach_bb84_cascade_stack(B, role=0)
        bb84_X, cascade_X = attach_bb84_cascade_stack(X, role=1)
        pair_bb84_protocols(bb84_B, bb84_X)
        pair_cascade_protocols(cascade_B, cascade_X)
        enable_bb84_metrics(bb84_B)
        enable_bb84_metrics(bb84_X)
        reset_metrics(bb84_B, bb84_X)
        protocols["BX"] = {"B": (bb84_B, cascade_B), "X": (bb84_X, cascade_X)}
        cascade_B.push(keysize, frame_num=1, run_time=int(40e9))

    def capture_BX():
        bb84_B, cascade_B = protocols["BX"]["B"]
        bb84_X, cascade_X = protocols["BX"]["X"]

        # BB84 keys
        print(f"\n[CAPTURE] B-{route} keys:")
        print("B BB84 key:", bb84_B.key)
        print(f"{route} BB84 key:", bb84_X.key)

        # Cascade corrected keys
        cascade_key_B = get_cascade_key(cascade_B, keysize)
        cascade_key_X = get_cascade_key(cascade_X, keysize)
        print("\nB Cascade key:", cascade_key_B)
        print(f"{route} Cascade key:", cascade_key_X)

        store["K_BX_B"] = cascade_key_B
        store["K_BX_X"] = cascade_key_X

        print(f"\n[METRICS] B -> {route}")
        print("Photons emitted at B:", bb84_B.photons_sent)
        print(f"Photons captured at {route}:", bb84_X.photons_received)
        qber = bb84_B.error_rates[-1] if hasattr(bb84_B, 'error_rates') and bb84_B.error_rates else None
        print(f"QBER (B-{route}):", qber)

    # X <-> F
    def start_XF():
        X = C if route == "C" else D
        reset_node_protocols(X)
        bb84_X, cascade_X = attach_bb84_cascade_stack(X, role=0)
        bb84_F, cascade_F = attach_bb84_cascade_stack(F, role=1)
        pair_bb84_protocols(bb84_X, bb84_F)
        pair_cascade_protocols(cascade_X, cascade_F)
        enable_bb84_metrics(bb84_X)
        enable_bb84_metrics(bb84_F)
        reset_metrics(bb84_X, bb84_F)
        protocols["XF"] = {"X": (bb84_X, cascade_X), "F": (bb84_F, cascade_F)}
        cascade_X.push(keysize, frame_num=1, run_time=int(40e9))

    def capture_XF():
        bb84_X, cascade_X = protocols["XF"]["X"]
        bb84_F, cascade_F = protocols["XF"]["F"]

        # BB84 keys
        print(f"\n[CAPTURE] {route}-F keys:")
        print(f"{route} BB84 key:", bb84_X.key)
        print("F BB84 key:", bb84_F.key)

        # Cascade corrected keys
        cascade_key_X = get_cascade_key(cascade_X, keysize)
        cascade_key_F = get_cascade_key(cascade_F, keysize)
        print(f"\n{route} Cascade key:", cascade_key_X)
        print("F Cascade key:", cascade_key_F)

        store["K_XF_X"] = cascade_key_X
        store["K_XF_F"] = cascade_key_F

        print(f"\n[METRICS] {route} -> F")
        print(f"Photons emitted at {route}:", bb84_X.photons_sent)
        print("Photons captured at F:", bb84_F.photons_received)
        qber = bb84_X.error_rates[-1] if hasattr(bb84_X, 'error_rates') and bb84_X.error_rates else None
        print(f"QBER ({route}-F):", qber)

    # Schedule
    tl.schedule(Event(0, Process(Runner(start_AB), "run", [])))
    tl.schedule(Event(int(60e9), Process(Runner(capture_AB), "run", [])))
    tl.schedule(Event(int(100e9), Process(Runner(start_BX), "run", [])))
    tl.schedule(Event(int(160e9), Process(Runner(capture_BX), "run", [])))
    tl.schedule(Event(int(200e9), Process(Runner(start_XF), "run", [])))
    tl.schedule(Event(int(260e9), Process(Runner(capture_XF), "run", [])))

    print(f"\n=== RUN: A -> F via B and {route} (trusted relays) ===")
    start = time.time()
    tl.init()
    tl.run()
    print("Finished in %.2f sec" % (time.time() - start))

    # Validate keys using Cascade keys
    K_AB_A, K_AB_B = store.get("K_AB_A"), store.get("K_AB_B")
    K_BX_B, K_BX_X = store.get("K_BX_B"), store.get("K_BX_X")
    K_XF_X, K_XF_F = store.get("K_XF_X"), store.get("K_XF_F")

    ok_ab = (K_AB_A is not None and K_AB_A == K_AB_B)
    ok_bx = (K_BX_B is not None and K_BX_B == K_BX_X)
    ok_xf = (K_XF_X is not None and K_XF_X == K_XF_F)

    print("\n=== LINK STATUS ===")
    print("AB established:", ok_ab)
    print(f"B-{route} established:", ok_bx)
    print(f"{route}-F established:", ok_xf)

    if not (ok_ab and ok_bx and ok_xf):
        print("Relay skipped: one or more link keys not correct.")
        return

    msg = b"HELLO F (via C)" if route == "C" else b"HELLO F (via D)"

    cipher1 = xor_encrypt(msg, K_AB_A)
    plainB = xor_encrypt(cipher1, K_AB_B)
    cipher2 = xor_encrypt(plainB, K_BX_B)
    plainX = xor_encrypt(cipher2, K_BX_X)
    cipher3 = xor_encrypt(plainX, K_XF_X)
    plainF = xor_encrypt(cipher3, K_XF_F)

    print("\n=== TRUSTED RELAY (3 hops) ===")
    print("Original:", msg)
    print("Delivered at F:", plainF)
    print("Correct:", plainF == msg)


if __name__ == "__main__":
    run(route="C")
    # run(route="D")
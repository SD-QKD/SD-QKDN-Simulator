import time
import math
import random
import numpy as np

from sequence.components.photon import Photon
from sequence.kernel.entity import Entity
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


def connect(tl, n1, n2, label, distance=1000, attenuation=0.0002, pol_fid=0.85):
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


def connect_classical_only(tl, n1, n2, label, distance=1000):
    ClassicalChannel(f"cc_{label}_1", tl, distance=distance).set_ends(n1, n2.name)
    ClassicalChannel(f"cc_{label}_2", tl, distance=distance).set_ends(n2, n1.name)


# Attach BB84 + Cascade stack properly
def attach_bb84_cascade_stack(node: QKDNode):
    """Attach BB84 and Cascade protocols to a node with proper connections."""
    if len(node.protocol_stack) >= 2 and node.protocol_stack[0] is not None:
        return node.protocol_stack[0], node.protocol_stack[1]

    # Ensure stack exists
    if len(node.protocol_stack) < 2:
        node.protocol_stack = [None, None]

    ls_name = f"{node.name}.lightsource"
    det_name = f"{node.name}.qsdetector"

    # Create protocols
    bb84 = BB84(node, f"{node.name}.BB84", ls_name, det_name)
    cascade = Cascade(node, f"{node.name}.cascade")

    # Add to stack
    node.protocol_stack[0] = bb84
    node.protocol_stack[1] = cascade

    # Add to protocols list
    node.protocols.append(bb84)
    node.protocols.append(cascade)

    # Connect protocols (BB84 is lower, Cascade is upper)
    bb84.upper_protocols.append(cascade)
    cascade.lower_protocols.append(bb84)

    return bb84, cascade


# Metrics: photons sent/received and error rates
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
    bb84_sender.error_rates = []
    bb84_receiver.error_rates = []


def compare_keys(key1, key2, keylen):
    """Compare two keys bit by bit and return error count."""
    if key1 is None or key2 is None:
        return None, None
    
    errors = 0
    for i in range(keylen):
        bit1 = (key1 >> i) & 1
        bit2 = (key2 >> i) & 1
        if bit1 != bit2:
            errors += 1
    
    error_rate = errors / keylen if keylen > 0 else 0
    return errors, error_rate


class InterceptResend:
    def __init__(self, p_attack=1.0):
        self.enabled = True
        self.p_attack = p_attack
        self.attacked = 0
        self.forwarded = 0

    def intercept(self, photon: Photon) -> Photon:
        self.forwarded += 1

        if (not self.enabled) or (random.random() > self.p_attack):
            return photon  # untouched forward

        self.attacked += 1

        eve_basis = random.randint(0, 1)
        eve_bit = random.randint(0, 1)

        new_photon = Photon(
            name=f"Eve_{self.attacked}",
            timeline=photon.timeline,
            wavelength=photon.wavelength,
            location="Eve",
            encoding_type=photon.encoding_type
        )

        # Attach debugging info
        new_photon.eve_basis = eve_basis
        new_photon.eve_bit = eve_bit
        return new_photon


# A -> F via B and C/D
def run(route="C", keysize=128, runtime_ms=600):
    assert route in ("C", "D")

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = True

    # Nodes
    A = QKDNode("A", tl, stack_size=2)
    B = QKDNode("B", tl, stack_size=2)
    C = QKDNode("C", tl, stack_size=0)
    D = QKDNode("D", tl, stack_size=0)
    F = QKDNode("F", tl, stack_size=0)

    # Channels
    connect(tl, A, B, "AB")
    connect(tl, B, C, "BC")
    connect(tl, B, D, "BD")
    connect(tl, C, F, "CF")
    connect(tl, D, F, "DF")

    # Eve on A-B link
    eve = InterceptResend(p_attack=0.5)
    qc_AB = A.qchannels["B"]
    orig_transmit = qc_AB.transmit

    def eve_transmit(photon, *args, **kwargs):
        photon2 = eve.intercept(photon)
        return orig_transmit(photon2, *args, **kwargs)

    qc_AB.transmit = eve_transmit
    eve.enabled = False  # Eve OFF by default

    # Setup BB84 + Cascade for A and B
    bb84_A, cascade_A = attach_bb84_cascade_stack(A)
    bb84_B, cascade_B = attach_bb84_cascade_stack(B)
    
    enable_bb84_metrics(bb84_A)
    enable_bb84_metrics(bb84_B)
    
    # Pair protocols
    pair_bb84_protocols(bb84_A, bb84_B)
    pair_cascade_protocols(cascade_A, cascade_B)

    # Storage for generated keys
    store = {
        "K_AB_A": None, "K_AB_B": None,
        "K_BX_B": None, "K_BX_X": None,
        "K_XF_X": None, "K_XF_F": None,
        # BB84 raw keys (directly from BB84 protocol)
        "BB84_AB_A": None, "BB84_AB_B": None,
        "BB84_BX_B": None, "BB84_BX_X": None,
        "BB84_XF_X": None, "BB84_XF_F": None
    }

    class Runner:
        def __init__(self, fn):
            self.fn = fn
        def run(self):
            self.fn()

    # Phase 1: A <-> B
    def start_AB():
        print("\n[START] A-B key generation")
        reset_metrics(bb84_A, bb84_B)
        # Push to Cascade, which will trigger BB84
        cascade_A.push(keysize, frame_num=1, run_time=int(80e9))

    def capture_AB():
        # Get BB84 keys directly from BB84.key (the raw key BB84 generated)
        # Extract first keysize bits from the BB84 key
        if hasattr(bb84_A, 'key') and bb84_A.key is not None:
            store["BB84_AB_A"] = bb84_A.key & ((1 << keysize) - 1)
        else:
            store["BB84_AB_A"] = None
            
        if hasattr(bb84_B, 'key') and bb84_B.key is not None:
            store["BB84_AB_B"] = bb84_B.key & ((1 << keysize) - 1)
        else:
            store["BB84_AB_B"] = None
        
        # Get Cascade-corrected keys
        if cascade_A.valid_keys and cascade_B.valid_keys:
            store["K_AB_A"] = cascade_A.valid_keys[-1] if cascade_A.valid_keys else None
            store["K_AB_B"] = cascade_B.valid_keys[-1] if cascade_B.valid_keys else None
        else:
            store["K_AB_A"] = None
            store["K_AB_B"] = None

        print("\n[CAPTURE] AB keys:")
        print("=" * 70)
        print("BB84 RAW Keys (directly from BB84 protocol, BEFORE Cascade):")
        print(f"  A BB84 key: {store['BB84_AB_A']}")
        print(f"  B BB84 key: {store['BB84_AB_B']}")
        bb84_errors, bb84_error_rate = compare_keys(store['BB84_AB_A'], store['BB84_AB_B'], keysize)
        if bb84_errors is not None:
            print(f"  BB84 key errors: {bb84_errors}/{keysize} bits ({bb84_error_rate*100:.4f}%)")
            print(f"  Error positions: ", end="")
            if bb84_errors > 0 and bb84_errors <= 20:
                # Show position of each error bit
                error_positions = []
                for i in range(keysize):
                    bit_A = (store['BB84_AB_A'] >> i) & 1
                    bit_B = (store['BB84_AB_B'] >> i) & 1
                    if bit_A != bit_B:
                        error_positions.append(i)
                print(error_positions)
            elif bb84_errors > 20:
                print(f"[{bb84_errors} errors - too many to list]")
            else:
                print("[]")
        
        print("\nCascade-Corrected Keys (AFTER error correction):")
        print(f"  A corrected key: {store['K_AB_A']}")
        print(f"  B corrected key: {store['K_AB_B']}")
        print(f"  Keys match: {store['K_AB_A'] == store['K_AB_B'] if store['K_AB_A'] else False}")
        corrected_errors, corrected_error_rate = compare_keys(store['K_AB_A'], store['K_AB_B'], keysize)
        if corrected_errors is not None:
            print(f"  Corrected key errors: {corrected_errors}/{keysize} bits ({corrected_error_rate*100:.4f}%)")
        
        if bb84_errors is not None and corrected_errors is not None:
            print(f"\n  ✓ Cascade fixed {bb84_errors - corrected_errors} errors!")
        print("=" * 70)

        print("\n[METRICS] A -> B")
        print("Photons emitted at A:", bb84_A.photons_sent)
        print("Photons captured at B:", bb84_B.photons_received)
        qber = bb84_A.error_rates[-1] if bb84_A.error_rates else None
        print("QBER (AB):", qber)
        print("Cascade error bit rate:", cascade_A.error_bit_rate)

        print("\n[EVE STATS]")
        print("Intercepted:", eve.attacked)
        print("Forwarded:", eve.forwarded)
        if eve.forwarded > 0:
            print("% attack:", (eve.attacked * 100 / eve.forwarded))

    # Phase 2: B <-> X
    def start_BX():
        print(f"\n[START] B-{route} key generation")
        X = C if route == "C" else D
        bb84_X, cascade_X = attach_bb84_cascade_stack(X)
        enable_bb84_metrics(bb84_X)

        # CRITICAL: Need to reset B's protocols for new pairing
        # Clear previous pairing
        bb84_B.another = None
        cascade_B.another = None
        cascade_B.role = -1
        
        # Re-pair for B-X link
        pair_bb84_protocols(bb84_B, bb84_X)
        pair_cascade_protocols(cascade_B, cascade_X)
        reset_metrics(bb84_B, bb84_X)

        # COMPLETE Cascade state reset for B
        cascade_B.state = 0
        cascade_B.bits = []
        cascade_B.valid_keys = []
        cascade_B.frame_num = 1
        cascade_B.checksum_tables = [[]]
        cascade_B.another_checksums = [[]]
        cascade_B.index_to_block_id_lists = [[]]
        cascade_B.block_id_to_index_lists = [[]]
        cascade_B.end_time = math.inf
        cascade_B.start_time = None
        
        # COMPLETE Cascade state reset for X
        cascade_X.state = 0
        cascade_X.bits = []
        cascade_X.valid_keys = []
        cascade_X.checksum_tables = [[]]
        cascade_X.another_checksums = [[]]
        cascade_X.index_to_block_id_lists = [[]]
        cascade_X.block_id_to_index_lists = [[]]
        cascade_X.end_time = math.inf
        cascade_X.start_time = None

        cascade_B.push(keysize, frame_num=1, run_time=int(100e9))

    def capture_BX():
        X = C if route == "C" else D
        cascade_X = X.protocol_stack[1]
        bb84_X = X.protocol_stack[0]

        # Get BB84 keys directly from BB84 protocol
        if hasattr(bb84_B, 'key') and bb84_B.key is not None:
            store["BB84_BX_B"] = bb84_B.key & ((1 << keysize) - 1)
        else:
            store["BB84_BX_B"] = None
            
        if hasattr(bb84_X, 'key') and bb84_X.key is not None:
            store["BB84_BX_X"] = bb84_X.key & ((1 << keysize) - 1)
        else:
            store["BB84_BX_X"] = None

        # Get Cascade-corrected keys
        if cascade_B.valid_keys and cascade_X.valid_keys:
            store["K_BX_B"] = cascade_B.valid_keys[-1] if cascade_B.valid_keys else None
            store["K_BX_X"] = cascade_X.valid_keys[-1] if cascade_X.valid_keys else None
        else:
            store["K_BX_B"] = None
            store["K_BX_X"] = None

        print(f"\n[CAPTURE] B-{route} keys:")
        print("=" * 70)
        print("BB84 RAW Keys (directly from BB84 protocol, BEFORE Cascade):")
        print(f"  B BB84 key: {store['BB84_BX_B']}")
        print(f"  {route} BB84 key: {store['BB84_BX_X']}")
        bb84_errors, bb84_error_rate = compare_keys(store['BB84_BX_B'], store['BB84_BX_X'], keysize)
        if bb84_errors is not None:
            print(f"  BB84 key errors: {bb84_errors}/{keysize} bits ({bb84_error_rate*100:.4f}%)")
            print(f"  Error positions: ", end="")
            if bb84_errors > 0 and bb84_errors <= 20:
                error_positions = []
                for i in range(keysize):
                    bit_B = (store['BB84_BX_B'] >> i) & 1
                    bit_X = (store['BB84_BX_X'] >> i) & 1
                    if bit_B != bit_X:
                        error_positions.append(i)
                print(error_positions)
            elif bb84_errors > 20:
                print(f"[{bb84_errors} errors - too many to list]")
            else:
                print("[]")
        
        print("\nCascade-Corrected Keys (AFTER error correction):")
        print(f"  B corrected key: {store['K_BX_B']}")
        print(f"  {route} corrected key: {store['K_BX_X']}")
        print(f"  Keys match: {store['K_BX_B'] == store['K_BX_X'] if store['K_BX_B'] else False}")
        corrected_errors, corrected_error_rate = compare_keys(store['K_BX_B'], store['K_BX_X'], keysize)
        if corrected_errors is not None:
            print(f"  Corrected key errors: {corrected_errors}/{keysize} bits ({corrected_error_rate*100:.4f}%)")
        
        if bb84_errors is not None and corrected_errors is not None:
            print(f"\n  ✓ Cascade fixed {bb84_errors - corrected_errors} errors!")
        print("=" * 70)

        print(f"\n[METRICS] B -> {route}")
        print("Photons emitted at B:", bb84_B.photons_sent)
        print(f"Photons captured at {route}:", bb84_X.photons_received)
        qber = bb84_B.error_rates[-1] if bb84_B.error_rates else None
        print(f"QBER (B-{route}):", qber)
        print("Cascade error bit rate:", cascade_B.error_bit_rate)

    # Phase 3: X <-> F
    def start_XF():
        print(f"\n[START] {route}-F key generation")
        X = C if route == "C" else D
        bb84_X, cascade_X = X.protocol_stack[0], X.protocol_stack[1]
        bb84_F, cascade_F = attach_bb84_cascade_stack(F)

        enable_bb84_metrics(bb84_X)
        enable_bb84_metrics(bb84_F)

        # Reset X's protocols for new pairing
        bb84_X.another = None
        cascade_X.another = None
        cascade_X.role = -1
        
        pair_bb84_protocols(bb84_X, bb84_F)
        pair_cascade_protocols(cascade_X, cascade_F)
        reset_metrics(bb84_X, bb84_F)

        # COMPLETE Cascade state reset for X
        cascade_X.state = 0
        cascade_X.bits = []
        cascade_X.valid_keys = []
        cascade_X.frame_num = 1
        cascade_X.checksum_tables = [[]]
        cascade_X.another_checksums = [[]]
        cascade_X.index_to_block_id_lists = [[]]
        cascade_X.block_id_to_index_lists = [[]]
        cascade_X.end_time = math.inf
        cascade_X.start_time = None
        
        # COMPLETE Cascade state reset for F
        cascade_F.state = 0
        cascade_F.bits = []
        cascade_F.valid_keys = []
        cascade_F.checksum_tables = [[]]
        cascade_F.another_checksums = [[]]
        cascade_F.index_to_block_id_lists = [[]]
        cascade_F.block_id_to_index_lists = [[]]
        cascade_F.end_time = math.inf
        cascade_F.start_time = None

        cascade_X.push(keysize, frame_num=1, run_time=int(100e9))

    def capture_XF():
        X = C if route == "C" else D
        cascade_X = X.protocol_stack[1]
        cascade_F = F.protocol_stack[1]
        bb84_X = X.protocol_stack[0]
        bb84_F = F.protocol_stack[0]

        # Get BB84 keys directly from BB84 protocol
        if hasattr(bb84_X, 'key') and bb84_X.key is not None:
            store["BB84_XF_X"] = bb84_X.key & ((1 << keysize) - 1)
        else:
            store["BB84_XF_X"] = None
            
        if hasattr(bb84_F, 'key') and bb84_F.key is not None:
            store["BB84_XF_F"] = bb84_F.key & ((1 << keysize) - 1)
        else:
            store["BB84_XF_F"] = None

        # Get Cascade-corrected keys
        if cascade_X.valid_keys and cascade_F.valid_keys:
            store["K_XF_X"] = cascade_X.valid_keys[-1] if cascade_X.valid_keys else None
            store["K_XF_F"] = cascade_F.valid_keys[-1] if cascade_F.valid_keys else None
        else:
            store["K_XF_X"] = None
            store["K_XF_F"] = None

        print(f"\n[CAPTURE] {route}-F keys:")
        print("=" * 70)
        print("BB84 RAW Keys (directly from BB84 protocol, BEFORE Cascade):")
        print(f"  {route} BB84 key: {store['BB84_XF_X']}")
        print(f"  F BB84 key: {store['BB84_XF_F']}")
        bb84_errors, bb84_error_rate = compare_keys(store['BB84_XF_X'], store['BB84_XF_F'], keysize)
        if bb84_errors is not None:
            print(f"  BB84 key errors: {bb84_errors}/{keysize} bits ({bb84_error_rate*100:.4f}%)")
            print(f"  Error positions: ", end="")
            if bb84_errors > 0 and bb84_errors <= 20:
                error_positions = []
                for i in range(keysize):
                    bit_X = (store['BB84_XF_X'] >> i) & 1
                    bit_F = (store['BB84_XF_F'] >> i) & 1
                    if bit_X != bit_F:
                        error_positions.append(i)
                print(error_positions)
            elif bb84_errors > 20:
                print(f"[{bb84_errors} errors - too many to list]")
            else:
                print("[]")
        
        print("\nCascade-Corrected Keys (AFTER error correction):")
        print(f"  {route} corrected key: {store['K_XF_X']}")
        print(f"  F corrected key: {store['K_XF_F']}")
        print(f"  Keys match: {store['K_XF_X'] == store['K_XF_F'] if store['K_XF_X'] else False}")
        corrected_errors, corrected_error_rate = compare_keys(store['K_XF_X'], store['K_XF_F'], keysize)
        if corrected_errors is not None:
            print(f"  Corrected key errors: {corrected_errors}/{keysize} bits ({corrected_error_rate*100:.4f}%)")
        
        if bb84_errors is not None and corrected_errors is not None:
            print(f"\n  ✓ Cascade fixed {bb84_errors - corrected_errors} errors!")
        print("=" * 70)

        print(f"\n[METRICS] {route} -> F")
        print(f"Photons emitted at {route}:", bb84_X.photons_sent)
        print("Photons captured at F:", bb84_F.photons_received)
        qber = bb84_X.error_rates[-1] if bb84_X.error_rates else None
        print(f"QBER ({route}-F):", qber)
        print("Cascade error bit rate:", cascade_X.error_bit_rate)

    # Schedule phases (adjusted timing for Cascade processing)
    # Phase 1: A-B (0 to 80ns)
    tl.schedule(Event(0, Process(Runner(start_AB), "run", [])))
    tl.schedule(Event(int(80e9), Process(Runner(capture_AB), "run", [])))

    # Phase 2: B-X (100ns to 200ns) - 100ns duration
    tl.schedule(Event(int(100e9), Process(Runner(start_BX), "run", [])))
    tl.schedule(Event(int(200e9), Process(Runner(capture_BX), "run", [])))

    # Phase 3: X-F (220ns to 320ns) - 100ns duration
    tl.schedule(Event(int(220e9), Process(Runner(start_XF), "run", [])))
    tl.schedule(Event(int(320e9), Process(Runner(capture_XF), "run", [])))

    # Run simulation
    print(f"\n=== RUN: A -> F via B and {route} (trusted relays with Cascade EC) ===")
    start = time.time()
    tl.init()
    tl.run()
    print("Finished in %.2f sec" % (time.time() - start))

    # Validate keys
    K_AB_A, K_AB_B = store["K_AB_A"], store["K_AB_B"]
    K_BX_B, K_BX_X = store["K_BX_B"], store["K_BX_X"]
    K_XF_X, K_XF_F = store["K_XF_X"], store["K_XF_F"]

    ok_ab = (K_AB_A is not None and K_AB_A == K_AB_B)
    ok_bx = (K_BX_B is not None and K_BX_B == K_BX_X)
    ok_xf = (K_XF_X is not None and K_XF_X == K_XF_F)

    print("\n=== LINK STATUS ===")
    print("AB established:", ok_ab)
    print(f"B-{route} established:", ok_bx)
    print(f"{route}-F established:", ok_xf)

    if not (ok_ab and ok_bx and ok_xf):
        print("\n[WARNING] Relay skipped: one or more link keys not established or don't match.")
        print("This may be due to insufficient runtime or Cascade error correction issues.")
        return

    # Trusted relay message
    msg = b"HELLO F (via C)" if route == "C" else b"HELLO F (via D)"

    # A -> B using AB
    cipher1 = xor_encrypt(msg, K_AB_A)
    plainB = xor_encrypt(cipher1, K_AB_B)

    # B -> X using BX
    cipher2 = xor_encrypt(plainB, K_BX_B)
    plainX = xor_encrypt(cipher2, K_BX_X)

    # X -> F using XF
    cipher3 = xor_encrypt(plainX, K_XF_X)
    plainF = xor_encrypt(cipher3, K_XF_F)

    print("\n=== TRUSTED RELAY (3 hops) ===")
    print("Original:", msg)
    print("Delivered at F:", plainF)
    print("Correct:", plainF == msg)


if __name__ == "__main__":
    run(route="C", keysize=128, runtime_ms=600)
    # run(route="D", keysize=128, runtime_ms=600)
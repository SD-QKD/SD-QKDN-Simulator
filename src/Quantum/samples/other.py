import time
import math
import random
import numpy as np

from sequence.components.photon import Photon
from sequence.kernel.entity import Entity
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

def connect_classical_only(tl, n1, n2, label, distance=1000):
    ClassicalChannel(f"cc_{label}_1", tl, distance=distance).set_ends(n1, n2.name)
    ClassicalChannel(f"cc_{label}_2", tl, distance=distance).set_ends(n2, n1.name)


# Attach BB84 (+ Cascade) dynamically 
def attach_bb84_stack2(node: QKDNode):
    if len(node.protocol_stack) >= 2 and node.protocol_stack[0] is not None:
        return node.protocol_stack[0]

    # Make sure stack exists
    if len(node.protocol_stack) < 2:
        node.protocol_stack = [None, None]

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


# Metrics: photons sent/received
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

        # attach debugging info
        new_photon.eve_basis = eve_basis
        new_photon.eve_bit = eve_bit
        return new_photon

def run_with_eve(route="C", keysize=1024, runtime_ms=1000):
    assert route in ("C", "D")

    tl = Timeline(runtime_ms * 1e9)
    tl.show_progress = True

    # Nodes
    A = QKDNode("A", tl, stack_size=2)
    Eve = QKDNode("Eve", tl, stack_size=2)   # 👈 Eve inserted
    B = QKDNode("B", tl, stack_size=2)

    C = QKDNode("C", tl, stack_size=0)
    D = QKDNode("D", tl, stack_size=0)
    F = QKDNode("F", tl, stack_size=0)

    # Channels
    connect(tl, A, Eve, "AE")     # A → Eve
    connect(tl, Eve, B, "EB")     # Eve → B

    connect(tl, B, C, "BC")
    connect(tl, B, D, "BD")
    connect(tl, C, F, "CF")
    connect(tl, D, F, "DF")

    # Attach BB84 stacks
    bb84_A = attach_bb84_stack2(A)
    bb84_E = attach_bb84_stack2(Eve)
    bb84_B = attach_bb84_stack2(B)

    enable_bb84_metrics(bb84_A)
    enable_bb84_metrics(bb84_E)
    enable_bb84_metrics(bb84_B)

    # Pair BB84 (this IS intercept–resend)
    pair_bb84_protocols(bb84_A, bb84_E)   # Alice ↔ Eve
    pair_bb84_protocols(bb84_E, bb84_B)   # Eve ↔ Bob

    store = {
        "K_A": None,
        "K_E1": None,
        "K_E2": None,
        "K_B": None
    }

    class Runner:
        def __init__(self, fn): self.fn = fn
        def run(self): self.fn()

    def start_AE_EB():
        bb84_A.push(keysize, 1)

    def capture_keys():
        store["K_A"]  = bb84_A.key
        store["K_E1"] = bb84_E.key
        store["K_B"]  = bb84_B.key

        print("\n[KEYS]")
        print("Alice key:", store["K_A"])
        print("Eve key  :", store["K_E1"])
        print("Bob key  :", store["K_B"])

        print("\n[QBER]")
        qber_AE = bb84_A.error_rates[-1] if bb84_A.error_rates else None
        qber_EB = bb84_E.error_rates[-1] if bb84_E.error_rates else None

        print("QBER (A–E):", qber_AE)
        print("QBER (E–B):", qber_EB)


        # Effective Alice–Bob QBER
        min_len = min(len(store["K_A"]), len(store["K_B"]))
        errors = sum(
            store["K_A"][i] != store["K_B"][i]
            for i in range(min_len)
        )
        qber_ab = errors / min_len if min_len > 0 else None

        print("Effective QBER (A–B):", qber_ab)

    # Schedule
    tl.schedule(Event(0, Process(Runner(start_AE_EB), "run", [])))
    tl.schedule(Event(int(200e9), Process(Runner(capture_keys), "run", [])))

    print("\n=== RUN: Eve between A and B ===")
    tl.init()
    tl.run()



if __name__ == "__main__":
    run_with_eve(route="C")
    # run_with_eve(route="D")  

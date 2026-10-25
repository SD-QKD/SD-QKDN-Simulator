import math

from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.kernel.event import Event
from sequence.kernel.process import Process
from sequence.kernel.timeline import Timeline
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.node import QKDNode
import sequence.utils.log as log


# constants
log_filename = "bb84.log"
runtime = 2e10
distance = 1e3

tl = Timeline(runtime)
tl.show_progress = True

# set log
log.set_logger(__name__, tl, log_filename)
log.set_logger_level('DEBUG')
log.track_module('BB84')
# log.track_module('timeline')
log.track_module('light_source')

qc0 = QuantumChannel("qc0", tl, distance=distance, polarization_fidelity=0.97, attenuation=0.0002)
qc1 = QuantumChannel("qc1", tl, distance=distance, polarization_fidelity=0.97, attenuation=0.0002)
cc0 = ClassicalChannel("cc0", tl, distance=distance)
cc1 = ClassicalChannel("cc1", tl, distance=distance)
cc0.delay += 1e9  # 1 ms
cc1.delay += 1e9

# Alice
ls_params = {"frequency": 80e6, "mean_photon_num": 0.1}
alice = QKDNode("alice", tl, stack_size=1)
alice.set_seed(0)

for name, param in ls_params.items():
    alice.update_lightsource_params(name, param)

# Bob
detector_params = [{"efficiency": 0.8, "dark_count": 10, "time_resolution": 10, "count_rate": 50e6},
                   {"efficiency": 0.8, "dark_count": 10, "time_resolution": 10, "count_rate": 50e6}]
bob = QKDNode("bob", tl, stack_size=1)
bob.set_seed(1)

for i in range(len(detector_params)):
    for name, param in detector_params[i].items():
        bob.update_detector_params(i, name, param)

qc0.set_ends(alice, bob.name)
qc1.set_ends(bob, alice.name)
cc0.set_ends(alice, bob.name)
cc1.set_ends(bob, alice.name)

# BB84 config
pair_bb84_protocols(alice.protocol_stack[0], bob.protocol_stack[0])

process = Process(alice.protocol_stack[0], "push", [256, math.inf, 6e12])
event = Event(0, process)
tl.schedule(event)

tl.init()
tl.run()

print("Alice key:", alice.protocol_stack[0].key)
print("Bob key:  ", bob.protocol_stack[0].key)
print("Keys match:", alice.protocol_stack[0].key == bob.protocol_stack[0].key)
print("Key length:", alice.protocol_stack[0].key.bit_length())

##############################################################
def int_to_bits(x, length):
    return bin(x)[2:].zfill(length)

raw_len = 256  # requested key length

alice_raw_bits = int_to_bits(alice.protocol_stack[0].key, raw_len)
bob_raw_bits   = int_to_bits(bob.protocol_stack[0].key, raw_len)

def parity(bits):
    return sum(bits) % 2

def cascade_correct(alice_bits, bob_bits, block_size=16, rounds=4):
    alice = list(map(int, alice_bits))
    bob   = list(map(int, bob_bits))

    n = len(alice)

    for r in range(rounds):
        for i in range(0, n, block_size):
            a_block = alice[i:i+block_size]
            b_block = bob[i:i+block_size]

            if parity(a_block) != parity(b_block):
                # binary search for error
                l, h = 0, len(a_block) - 1
                while l < h:
                    m = (l + h) // 2
                    if parity(a_block[l:m+1]) != parity(b_block[l:m+1]):
                        h = m
                    else:
                        l = m + 1
                # flip Bob's erroneous bit
                bob[i + l] ^= 1

        block_size *= 2  # Cascade increases block size

    return "".join(map(str, alice)), "".join(map(str, bob))

alice_corr_bits, bob_corr_bits = cascade_correct(
    alice_raw_bits, bob_raw_bits
)


import hashlib

def privacy_amplification(bits, final_len=128):
    bit_bytes = int(bits, 2).to_bytes(len(bits) // 8, 'big')
    digest = hashlib.sha256(bit_bytes).digest()
    final_key = int.from_bytes(digest, 'big')
    return bin(final_key)[2:].zfill(256)[:final_len]


alice_final = privacy_amplification(alice_corr_bits, 128)
bob_final   = privacy_amplification(bob_corr_bits, 128)

print("\nFinal secret key:")
print("Alice:", alice_final)
print("Bob:  ", bob_final)
print("Final keys match:", alice_final == bob_final)
print("Final key length:", len(alice_final))

print("After error correction:")
print("Keys match:", alice_corr_bits == bob_corr_bits)

def compute_qber(a, b):
    errors = sum(x != y for x, y in zip(a, b))
    return errors / len(a)

qber = compute_qber(alice_raw_bits, bob_raw_bits)
print(f"Estimated QBER: {qber:.4%}")

#############################################################################
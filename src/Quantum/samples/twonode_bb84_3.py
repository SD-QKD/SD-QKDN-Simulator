import time
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
import sequence.utils.log as log

# -------------------------------
# Basic 2-node BB84 topology
# -------------------------------

def run_bb84(sim_time_ms=10, keysize=256):

    # 1. Timeline (ms → ps)
    tl = Timeline(sim_time_ms * 1e9)
    tl.show_progress = True

    # 2. Setup logging
    log_filename = "bb84_simulation.log"
    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level("DEBUG")

    # Track important BB84 internals
    log.track_module("BB84")
    log.track_module("light_source")
    log.track_module("quantum_channel")
    log.track_module("classical_channel")

    # 3. Create Alice and Bob
    alice = QKDNode("alice", tl, stack_size=1)
    bob   = QKDNode("bob", tl, stack_size=1)

    alice.set_seed(0)
    bob.set_seed(1)

    # 4. Pair BB84 protocols
    pair_bb84_protocols(
        alice.protocol_stack[0],
        bob.protocol_stack[0]
    )

    # 5. Classical channels
    cc_ab = ClassicalChannel("cc_ab", tl, distance=1e3)
    cc_ba = ClassicalChannel("cc_ba", tl, distance=1e3)

    cc_ab.set_ends(alice, bob.name)
    cc_ba.set_ends(bob, alice.name)

    # 6. Quantum channels
    qc_ab = QuantumChannel(
        "qc_ab",
        tl,
        distance=1e3,
        attenuation=1e-5,
        polarization_fidelity=1
    )
    qc_ba = QuantumChannel(
        "qc_ba",
        tl,
        distance=1e3,
        attenuation=1e-5,
        polarization_fidelity=1
    )

    qc_ab.set_ends(alice, bob.name)
    qc_ba.set_ends(bob, alice.name)

    # 7. Initialize simulation
    tl.init()

    # 8. Request ONE key
    alice.protocol_stack[0].push(keysize, 1)

    print("Running BB84 simulation...")
    start = time.time()
    tl.run()
    print("Simulation finished in %.2f sec" % (time.time() - start))

    # 9. Print final keys
    alice_key = alice.protocol_stack[0].key
    bob_key   = bob.protocol_stack[0].key

    print("\n=== FINAL SECRET KEY ===")
    print("Alice key:", alice.protocol_stack[0].key, alice.protocol_stack[0].key.bit_length())
    print("Bob   key:", bob.protocol_stack[0].key, alice.protocol_stack[0].key.bit_length())
    # format(alice_key, f'0{keysize}b')
    print("Keys match:", alice_key == bob_key)

    # 10. Print QBER
    if alice.protocol_stack[0].error_rates:
        print("\nQBER:",
              alice.protocol_stack[0].error_rates[0] * 100, "%")
        
    # 11. Print Key Rate
    sim_time_sec = sim_time_ms / 1000

    final_bits = alice.protocol_stack[0].key.bit_length()

    key_rate = final_bits / sim_time_sec

    print("\n=== KEY RATE ===")
    print(f"Final key bits: {final_bits}")
    print(f"Simulation time: {sim_time_sec:.3f} s")
    print(f"Secure key rate: {key_rate:.2f} bits/s")


    print("\nLog file saved as:", log_filename)


# -------------------------------
# Run
# -------------------------------
if __name__ == "__main__":
    run_bb84(sim_time_ms=10, keysize=256)

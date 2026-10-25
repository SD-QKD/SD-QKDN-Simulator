import time
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
import sequence.utils.log as log


# --------------------------------------------------
# Helper: OTP XOR encryption/decryption using int key
# --------------------------------------------------
def xor_encrypt(msg_bytes: bytes, key_int: int) -> bytes:
    """One-time-pad style XOR with key material derived from int key."""
    if key_int is None:
        raise ValueError("Key is None (protocol may have failed/aborted).")

    # convert int key → bytes
    key_bytes = key_int.to_bytes((key_int.bit_length() + 7) // 8, "big")
    if len(key_bytes) == 0:
        raise ValueError("Key length is 0 bits.")

    # repeat key to match message length
    full_key = (key_bytes * ((len(msg_bytes) // len(key_bytes)) + 1))[:len(msg_bytes)]

    return bytes([m ^ k for m, k in zip(msg_bytes, full_key)])


def run_topology(sim_time_ms=20, keysize=256):

    # 1. Timeline
    tl = Timeline(sim_time_ms * 1e9)

    # 2. Setup logging
    log_filename = "bb84_simulation.log"
    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level("DEBUG")

    # Track important BB84 internals
    log.track_module("BB84")
    log.track_module("light_source")
    log.track_module("quantum_channel")
    log.track_module("classical_channel")

    # 3. Create nodes
    A = QKDNode("A", tl, stack_size=1)

    # B is split into 3 physical QKD interfaces
    B_AB = QKDNode("B_AB", tl, stack_size=1)
    B_BC = QKDNode("B_BC", tl, stack_size=1)
    B_BD = QKDNode("B_BD", tl, stack_size=1)

    C = QKDNode("C", tl, stack_size=1)
    D = QKDNode("D", tl, stack_size=1)

    # Seeds
    A.set_seed(0)
    B_AB.set_seed(1)
    B_BC.set_seed(2)
    B_BD.set_seed(3)
    C.set_seed(4)
    D.set_seed(5)

    # 4. Pair BB84 protocols (one per physical link)
    pair_bb84_protocols(A.protocol_stack[0], B_AB.protocol_stack[0])   # A–B
    pair_bb84_protocols(B_BC.protocol_stack[0], C.protocol_stack[0])   # B–C
    pair_bb84_protocols(B_BD.protocol_stack[0], D.protocol_stack[0])   # B–D

    # --------------------------------------------------
    # 5. Channels
    # --------------------------------------------------
    def connect(n1, n2, label):
        QuantumChannel(
            f"qc_{label}_1", tl,
            distance=1e6,
            attenuation=1e-5,
            polarization_fidelity=1
        ).set_ends(n1, n2.name)

        QuantumChannel(
            f"qc_{label}_2", tl,
            distance=1e6,
            attenuation=1e-5,
            polarization_fidelity=1
        ).set_ends(n2, n1.name)

        ClassicalChannel(f"cc_{label}_1", tl, distance=1e3).set_ends(n1, n2.name)
        ClassicalChannel(f"cc_{label}_2", tl, distance=1e3).set_ends(n2, n1.name)

    connect(A, B_AB, "AB")
    connect(B_BC, C, "BC")
    connect(B_BD, D, "BD")

    # 6. Initialize simulation
    tl.init()

    # 7. Request one key per link
    A.protocol_stack[0].push(keysize, 1)       # A–B key
    B_BC.protocol_stack[0].push(keysize, 1)    # B–C key
    B_BD.protocol_stack[0].push(keysize, 1)    # B–D key

    print("Running 4-node topology simulation...")
    start = time.time()
    tl.run()
    print("Finished in %.2f sec\n" % (time.time() - start))

    # --------------------------------------------------
    # 8. Verification (link-level keys)
    # --------------------------------------------------
    K_AB_A = A.protocol_stack[0].key
    K_AB_B = B_AB.protocol_stack[0].key

    K_BC_B = B_BC.protocol_stack[0].key
    K_BC_C = C.protocol_stack[0].key

    K_BD_B = B_BD.protocol_stack[0].key
    K_BD_D = D.protocol_stack[0].key

    print("=== PRINT LINK KEYS ===")
    print("== A-B ==")
    print("A key: ", K_AB_A)
    print("B key: ", K_AB_B)

    print("== B-C ==")
    print("B key: ", K_BC_B)
    print("C key: ", K_BC_C)

    print("== B-D ==")
    print("B key: ", K_BD_B)
    print("D key: ", K_BD_D)

    print("\n=== KEY VERIFICATION ===")
    print("A–B match:", K_AB_A == K_AB_B)
    print("B–C match:", K_BC_B == K_BC_C)
    print("B–D match:", K_BD_B == K_BD_D)

    print("\n=== KEY LENGTHS ===")
    print("A–B:", K_AB_A.bit_length() if K_AB_A else None)
    print("B–C:", K_BC_B.bit_length() if K_BC_B else None)
    print("B–D:", K_BD_B.bit_length() if K_BD_B else None)

    # --------------------------------------------------
    # 9. TRUSTED RELAY DATA FORWARDING: A -> C via B
    # --------------------------------------------------
    print("\n==================================================")
    print("=== TRUSTED RELAY FORWARDING (A -> C via B) ===")
    print("==================================================")

    if not (K_AB_A and K_BC_B and (K_AB_A == K_AB_B) and (K_BC_B == K_BC_C)):
        print("Forwarding A->C skipped: link keys not established correctly.")
    else:
        message_c = b"HELLO C, THIS IS A"
        print("Original message:", message_c)

        # A encrypts with K_AB
        cipher1 = xor_encrypt(message_c, K_AB_A)
        print("A -> B (cipher1):", cipher1)

        # B decrypts with K_AB
        plaintext_at_B = xor_encrypt(cipher1, K_AB_B)
        print("B decrypts:", plaintext_at_B)

        # B re-encrypts with K_BC
        cipher2 = xor_encrypt(plaintext_at_B, K_BC_B)
        print("B -> C (cipher2):", cipher2)

        # C decrypts with K_BC
        plaintext_at_C = xor_encrypt(cipher2, K_BC_C)
        print("C decrypts:", plaintext_at_C)

        print("\nDelivered correctly:", plaintext_at_C == message_c)

    # --------------------------------------------------
    # 10. TRUSTED RELAY DATA FORWARDING: A -> D via B
    # --------------------------------------------------
    print("\n==================================================")
    print("=== TRUSTED RELAY FORWARDING (A -> D via B) ===")
    print("==================================================")

    if not (K_AB_A and K_BD_B and (K_AB_A == K_AB_B) and (K_BD_B == K_BD_D)):
        print("Forwarding A->D skipped: link keys not established correctly.")
    else:
        message_d = b"HELLO D, THIS IS A"
        print("Original message:", message_d)

        # A encrypts with K_AB
        cipher1_d = xor_encrypt(message_d, K_AB_A)
        print("A -> B (cipher1):", cipher1_d)

        # B decrypts with K_AB
        plaintext_at_B_d = xor_encrypt(cipher1_d, K_AB_B)
        print("B decrypts:", plaintext_at_B_d)

        # B re-encrypts with K_BD
        cipher2_d = xor_encrypt(plaintext_at_B_d, K_BD_B)
        print("B -> D (cipher2):", cipher2_d)

        # D decrypts with K_BD
        plaintext_at_D = xor_encrypt(cipher2_d, K_BD_D)
        print("D decrypts:", plaintext_at_D)

        print("\nDelivered correctly:", plaintext_at_D == message_d)


# --------------------------------------------------
# Run
# --------------------------------------------------
if __name__ == "__main__":
    run_topology()

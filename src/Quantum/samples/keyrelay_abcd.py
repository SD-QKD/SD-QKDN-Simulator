import time
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
import sequence.utils.log as log



# XOR encryption/decryption using int key
def xor_encrypt(data: bytes, key_int: int) -> bytes:
    """
    One-time-pad style XOR with key material derived from int key.
    Same function encrypts and decrypts.
    """
    if key_int is None:
        raise ValueError("Key is None (BB84 may have failed).")

    key_bytes = key_int.to_bytes((key_int.bit_length() + 7) // 8, "big")
    if len(key_bytes) == 0:
        raise ValueError("Key length is 0 bits.")

    # Repeat key to match message length
    repeated_key = (key_bytes * ((len(data) // len(key_bytes)) + 1))[:len(data)]
    return bytes([b ^ k for b, k in zip(data, repeated_key)])


# Trusted relay: common A->B then route B->(C/D)
def trusted_relay_from_A(
    destination: str,
    plaintext: bytes,
    key_AB_at_A: int,
    key_AB_at_B: int,
    outbound_key_at_B: int,
    outbound_key_at_dest: int
):
    """
    Trusted relay flow:
        A encrypts with AB key -> send to B
        B decrypts with AB key
        B encrypts with destination key (BC or BD)
        Destination decrypts with destination key
    """

    print("\n==================================================")
    print(f"=== TRUSTED RELAY: A -> {destination} (via B) ===")
    print("==================================================")
    print("Original plaintext:", plaintext)

    # -------------------------
    # COMMON PART: A -> B
    # -------------------------
    ciphertext_A_to_B = xor_encrypt(plaintext, key_AB_at_A)
    # --- ATTACK / ERROR: flip 1 bit in ciphertext_A_to_B ---
    # ciphertext_A_to_B = bytearray(ciphertext_A_to_B)
    # ciphertext_A_to_B[0] ^= 0x01   # flip the least significant bit of first byte
    # ciphertext_A_to_B = bytes(ciphertext_A_to_B)
    print("A -> B ciphertext:", ciphertext_A_to_B)

    plaintext_at_B = xor_encrypt(ciphertext_A_to_B, key_AB_at_B)
    # plaintext_at_B = xor_encrypt(ciphertext_A_to_B, outbound_key_at_B)  # WRONG key on purpose
    print("B decrypts plaintext:", plaintext_at_B)


    # ROUTING PART: B -> DEST
    ciphertext_B_to_dest = xor_encrypt(plaintext_at_B, outbound_key_at_B)
    print(f"B -> {destination} ciphertext:", ciphertext_B_to_dest)

    plaintext_at_dest = xor_encrypt(ciphertext_B_to_dest, outbound_key_at_dest)
    print(f"{destination} decrypts plaintext:", plaintext_at_dest)

    print("\nDelivered correctly:", plaintext_at_dest == plaintext)


def run_topology(sim_time_ms=20, keysize=256):

    # Create simulation timeline (ms -> ps)
    timeline = Timeline(sim_time_ms * 1e9)

    # Setup logging
    log_filename = "bb84_simulation.log"
    log.set_logger(__name__, timeline, log_filename)
    log.set_logger_level("DEBUG")

    log.track_module("BB84")
    log.track_module("light_source")
    log.track_module("quantum_channel")
    log.track_module("classical_channel")

    # Create nodes (A, C, D) and B's physical ports
    A = QKDNode("A", timeline, stack_size=1)

    # B is a trusted relay site with three physical QKD interfaces (ports)
    B_AB = QKDNode("B_AB", timeline, stack_size=1)
    B_BC = QKDNode("B_BC", timeline, stack_size=1)
    B_BD = QKDNode("B_BD", timeline, stack_size=1)

    C = QKDNode("C", timeline, stack_size=1)
    D = QKDNode("D", timeline, stack_size=1)

    A.set_seed(0)
    B_AB.set_seed(1)
    B_BC.set_seed(2)
    B_BD.set_seed(3)
    C.set_seed(4)
    D.set_seed(5)

    # Pair BB84 protocols (one per link)
    pair_bb84_protocols(A.protocol_stack[0], B_AB.protocol_stack[0])  # A <-> B
    pair_bb84_protocols(B_BC.protocol_stack[0], C.protocol_stack[0])  # B <-> C
    pair_bb84_protocols(B_BD.protocol_stack[0], D.protocol_stack[0])  # B <-> D

    # Connect channels
    def connect_link(n1, n2, label):
        # Quantum channels 
        QuantumChannel(f"qc_{label}_1", timeline, distance=1e6, attenuation=1e-5, polarization_fidelity=1)\
            .set_ends(n1, n2.name)
        QuantumChannel(f"qc_{label}_2", timeline, distance=1e6, attenuation=1e-5, polarization_fidelity=1)\
            .set_ends(n2, n1.name)

        # Classical channels 
        ClassicalChannel(f"cc_{label}_1", timeline, distance=1e3).set_ends(n1, n2.name)
        ClassicalChannel(f"cc_{label}_2", timeline, distance=1e3).set_ends(n2, n1.name)

    connect_link(A, B_AB, "AB")
    connect_link(B_BC, C, "BC")
    connect_link(B_BD, D, "BD")

    # Initialize simulation
    timeline.init()

    # Request keys
    A.protocol_stack[0].push(keysize, 1)       # AB key
    B_BC.protocol_stack[0].push(keysize, 1)  # BC key
    B_BD.protocol_stack[0].push(keysize, 1)  # BD key

    print("\nRunning 4-node topology simulation...")
    start = time.time()
    timeline.run()
    print("Finished in %.2f sec\n" % (time.time() - start))

    # Extract keys from protocols
    key_AB_at_A = A.protocol_stack[0].key
    key_AB_at_B = B_AB.protocol_stack[0].key

    key_BC_at_B = B_BC.protocol_stack[0].key
    key_BC_at_C = C.protocol_stack[0].key

    key_BD_at_B = B_BD.protocol_stack[0].key
    key_BD_at_D = D.protocol_stack[0].key

    # Verify link-level keys
    print("=== PRINT KEY ===")
    print("== A-B ==")
    print("A key: ", A.protocol_stack[0].key)
    print("B_AB key: ", B_AB.protocol_stack[0].key)

    print("== B-C ==")
    print("B_BC key: ", B_BC.protocol_stack[0].key)
    print("C key: ", C.protocol_stack[0].key)

    print("== B-D ==")
    print("B_BD key: ", B_BD.protocol_stack[0].key)
    print("D key: ", D.protocol_stack[0].key)

    
    print("=== LINK KEY VERIFICATION ===")
    print("A-B match:", key_AB_at_A == key_AB_at_B)
    print("B-C match:", key_BC_at_B == key_BC_at_C)
    print("B-D match:", key_BD_at_B == key_BD_at_D)

    # Trusted relay routing choice
    destination = "D"   
    message = b"HELLO, THIS IS A"

    # AB must be valid first
    if not (key_AB_at_A and key_AB_at_B and (key_AB_at_A == key_AB_at_B)):
        print("\nRouting skipped: AB key not established correctly.")
        return

    if destination == "C":
        if not (key_BC_at_B and key_BC_at_C and (key_BC_at_B == key_BC_at_C)):
            print("\nRouting to C skipped: BC key not established correctly.")
            return

        trusted_relay_from_A(
            destination="C",
            plaintext=message,
            key_AB_at_A=key_AB_at_A,
            key_AB_at_B=key_AB_at_B,
            outbound_key_at_B=key_BC_at_B,
            outbound_key_at_dest=key_BC_at_C
        )

    elif destination == "D":
        if not (key_BD_at_B and key_BD_at_D and (key_BD_at_B == key_BD_at_D)):
            print("\nRouting to D skipped: BD key not established correctly.")
            return

        trusted_relay_from_A(
            destination="D",
            plaintext=message,
            key_AB_at_A=key_AB_at_A,
            key_AB_at_B=key_AB_at_B,
            outbound_key_at_B=key_BD_at_B,
            outbound_key_at_dest=key_BD_at_D
        )

    else:
        print("\nUnknown destination:", destination)

    print("\nLog file saved as:", log_filename)

# Run
if __name__ == "__main__":
    run_topology()

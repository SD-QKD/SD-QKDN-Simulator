import time
from dataclasses import dataclass

from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
import sequence.utils.log as log



# XOR encryption/decryption
def xor_encrypt(data: bytes, key_int: int) -> bytes:
    """OTP-style XOR using key material derived from BB84 integer key."""
    if key_int is None:
        raise ValueError("Key is None (BB84 may have failed).")

    key_bytes = key_int.to_bytes((key_int.bit_length() + 7) // 8, "big")
    if len(key_bytes) == 0:
        raise ValueError("Key length is 0 bits.")

    repeated_key = (key_bytes * ((len(data) // len(key_bytes)) + 1))[:len(data)]
    return bytes([b ^ k for b, k in zip(data, repeated_key)])


# One logical Trusted Relay Site B with 3 physical ports
@dataclass
class BPorts:
    AB: QKDNode
    BC: QKDNode
    BD: QKDNode


class TrustedRelayB:
    """
    ONE logical trusted relay site B.

    Internally has 3 physical QKD terminals (ports), each modeled as a QKDNode:
      - port AB forms key with A
      - port BC forms key with C
      - port BD forms key with D

    The "KMS/controller" behavior is implemented here (forwarding).
    """

    def __init__(self, tl: Timeline):
        self.ports = BPorts(
            AB=QKDNode("B_AB", tl, stack_size=1),
            BC=QKDNode("B_BC", tl, stack_size=1),
            BD=QKDNode("B_BD", tl, stack_size=1),
        )

    def set_seeds(self, base=100):
        self.ports.AB.set_seed(base + 1)
        self.ports.BC.set_seed(base + 2)
        self.ports.BD.set_seed(base + 3)

    def get_key_AB(self):
        return self.ports.AB.protocol_stack[0].key

    def get_key_BC(self):
        return self.ports.BC.protocol_stack[0].key

    def get_key_BD(self):
        return self.ports.BD.protocol_stack[0].key

    def forward(self, ciphertext_from_A: bytes, dest: str) -> bytes:
        """
        Trusted relay forwarding:

        1) decrypt using K_AB at port AB
        2) encrypt using K_BC or K_BD at the correct outbound port
        """
        k_ab = self.get_key_AB()
        if k_ab is None:
            raise RuntimeError("AB key missing at B. Can't relay.")

        plaintext = xor_encrypt(ciphertext_from_A, k_ab)

        if dest == "C":
            k_out = self.get_key_BC()
            if k_out is None:
                raise RuntimeError("BC key missing at B. Can't relay to C.")
            return xor_encrypt(plaintext, k_out)

        if dest == "D":
            k_out = self.get_key_BD()
            if k_out is None:
                raise RuntimeError("BD key missing at B. Can't relay to D.")
            return xor_encrypt(plaintext, k_out)

        raise ValueError("Destination must be 'C' or 'D'.")



# Channel connect helper
def connect_link(tl: Timeline, n1: QKDNode, n2: QKDNode, label: str,
                 qc_distance=1e3, attenuation=1e-90, pfid=1.0, cc_distance=1e3):

    # Quantum 
    QuantumChannel(f"qc_{label}_1", tl, distance=qc_distance,
                   attenuation=attenuation, polarization_fidelity=pfid).set_ends(n1, n2.name)
    QuantumChannel(f"qc_{label}_2", tl, distance=qc_distance,
                   attenuation=attenuation, polarization_fidelity=pfid).set_ends(n2, n1.name)

    # Classical 
    ClassicalChannel(f"cc_{label}_1", tl, distance=cc_distance).set_ends(n1, n2.name)
    ClassicalChannel(f"cc_{label}_2", tl, distance=cc_distance).set_ends(n2, n1.name)


# A - B - {C, D}
def run_topology(sim_time_ms=30, keysize=256, destination="D"):

    tl = Timeline(sim_time_ms * 1e9)

    # Logging 
    log_filename = "bb84_multiport.log"
    log.set_logger(__name__, tl, log_filename)
    log.set_logger_level("DEBUG")
    log.track_module("BB84")

    # Create endpoints
    A = QKDNode("A", tl, stack_size=1)
    C = QKDNode("C", tl, stack_size=1)
    D = QKDNode("D", tl, stack_size=1)

    A.set_seed(0)
    C.set_seed(4)
    D.set_seed(5)

    # Create ONE logical relay site B (3 ports)
    B = TrustedRelayB(tl)
    B.set_seeds(100)

    # Pair BB84 protocols 
    pair_bb84_protocols(A.protocol_stack[0], B.ports.AB.protocol_stack[0])  # A<->B
    pair_bb84_protocols(B.ports.BC.protocol_stack[0], C.protocol_stack[0])  # B<->C
    pair_bb84_protocols(B.ports.BD.protocol_stack[0], D.protocol_stack[0])  # B<->D

    # Connect channels
    connect_link(tl, A, B.ports.AB, "AB", qc_distance=1e3, pfid=1.0)
    connect_link(tl, B.ports.BC, C, "BC", qc_distance=1e3, pfid=1.0)
    connect_link(tl, B.ports.BD, D, "BD", qc_distance=1e3, pfid=1.0)

    # Init simulation
    tl.init()

    # Request keys
    A.protocol_stack[0].push(keysize, 1)               # AB key
    B.ports.BC.protocol_stack[0].push(keysize, 1)      # BC key
    B.ports.BD.protocol_stack[0].push(keysize, 1)      # BD key

    print("\nRunning 4-node topology with trusted relay B...")
    t0 = time.time()
    tl.run()
    print("Simulation finished in %.2f sec\n" % (time.time() - t0))

    # Extract and verify link keys
    K_AB_A = A.protocol_stack[0].key
    K_AB_B = B.ports.AB.protocol_stack[0].key

    K_BC_B = B.ports.BC.protocol_stack[0].key
    K_BC_C = C.protocol_stack[0].key

    K_BD_B = B.ports.BD.protocol_stack[0].key
    K_BD_D = D.protocol_stack[0].key

    print("=== PRINT KEY ===")
    print("== A-B ==")
    print("A key: ", K_AB_A)
    print("B_AB key: ", K_AB_B)

    print("== B-C ==")
    print("B_BC key: ", K_BC_B)
    print("C key: ", K_BC_C)

    print("== B-D ==")
    print("B_BD key: ", K_BD_B)
    print("D key: ", K_BD_D)

    print("=== LINK KEY VERIFICATION ===")
    print("A-B match:", K_AB_A == K_AB_B)
    print("B-C match:", K_BC_B == K_BC_C)
    print("B-D match:", K_BD_B == K_BD_D)

    # Trusted relay forwarding test
    print("\n==================================================")
    print(f"=== END-TO-END TRUSTED RELAY: A -> {destination} via B ===")
    print("==================================================")

    if not (K_AB_A and K_AB_B and K_AB_A == K_AB_B):
        print("Cannot relay: AB key not established correctly.")
        return

    message = b"HELLO, THIS IS A"
    print("Original plaintext:", message)

    cipher_to_B = xor_encrypt(message, K_AB_A)
    print("A -> B ciphertext:", cipher_to_B)

    cipher_to_dest = B.forward(cipher_to_B, destination)
    print(f"B -> {destination} ciphertext:", cipher_to_dest)

    if destination == "C":
        if not (K_BC_C and K_BC_B == K_BC_C):
            print("Cannot decrypt at C: BC key mismatch/missing.")
            return
        recovered = xor_encrypt(cipher_to_dest, K_BC_C)

    elif destination == "D":
        if not (K_BD_D and K_BD_B == K_BD_D):
            print("Cannot decrypt at D: BD key mismatch/missing.")
            return
        recovered = xor_encrypt(cipher_to_dest, K_BD_D)

    else:
        raise ValueError("destination must be 'C' or 'D'")

    print(f"{destination} decrypts plaintext:", recovered)
    print("Delivered correctly:", recovered == message)

    print("\nLog file saved as:", log_filename)


if __name__ == "__main__":
    run_topology(sim_time_ms=30, keysize=256, destination="D")

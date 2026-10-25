from typing import List
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.kernel.timeline import Timeline
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.topology.node import QKDNode


# -----------------------------
# helpers
# -----------------------------
def bits_to_bytes(bits: List[int]) -> bytes:
    out = bytearray()
    cur = 0
    cnt = 0
    for bit in bits:
        cur = (cur << 1) | (bit & 1)
        cnt += 1
        if cnt == 8:
            out.append(cur)
            cur = 0
            cnt = 0
    if cnt > 0:
        cur = cur << (8 - cnt)
        out.append(cur)
    return bytes(out)


def bytes_to_bits(data: bytes, bit_len: int) -> List[int]:
    bits = []
    for byte in data:
        for i in range(7, -1, -1):
            bits.append((byte >> i) & 1)
    return bits[:bit_len]


def xor_bytes(a: bytes, b: bytes) -> bytes:
    n = min(len(a), len(b))
    return bytes([a[i] ^ b[i] for i in range(n)])


def get_key_bits(node: QKDNode, peer: str) -> List[int]:
    """
    Fetch key bits produced with `peer`.
    Many SeQUeNCe versions store link keys in node.keys[peer].
    """
    if not hasattr(node, "keys") or peer not in node.keys:
        raise RuntimeError(f"Key not found at {node.name}.keys[{peer}]")

    k = node.keys[peer]

    # common formats
    if isinstance(k, list) and (len(k) == 0 or isinstance(k[0], int)):
        return k
    if isinstance(k, list) and len(k) > 0 and isinstance(k[0], list):
        return k[-1]

    raise RuntimeError(f"Unknown key format: {type(k)} => {k}")


# -----------------------------
# main
# -----------------------------
def run_bb84_ab_bc(runtime=2e10, distance=1e3, relay_bits=128):
    tl = Timeline(runtime)

    # nodes
    a = QKDNode("a", tl)
    b = QKDNode("b", tl)
    c = QKDNode("c", tl)

    # channels: A<->B
    q_ab = QuantumChannel("q_ab", tl, distance=distance, attenuation=1e3)
    c_ab = ClassicalChannel("c_ab", tl, distance=distance)
    q_ab.set_ends(a, b.name)
    c_ab.set_ends(a, b.name)

    # channels: B<->C
    q_bc = QuantumChannel("q_bc", tl, distance=distance, attenuation=1e3)
    c_bc = ClassicalChannel("c_bc", tl, distance=distance)
    q_bc.set_ends(b, c.name)
    c_bc.set_ends(b, c.name)

    # BB84 protocols on each link
    bb84_ab = pair_bb84_protocols(a, b, "q_ab", "q_ba", "c_ab", "c_ba")
    bb84_bc = pair_bb84_protocols(b, c, "q_bc", "q_cb", "c_bc", "c_cb")

    # start protocols
    for p in bb84_ab + bb84_bc:
        p.start()

    tl.init()
    tl.run()

    # -----------------------------
    # b acts as a QKD switch (trusted relay)
    # -----------------------------
    K_ab = get_key_bits(a, "b")
    K_bc = get_key_bits(b, "c")

    L = min(len(K_ab), len(K_bc), relay_bits)
    K_ab = K_ab[:L]
    K_bc = K_bc[:L]

    # b prepares relay message M = K_ab XOR K_bc
    # send M classically to c
    M = xor_bytes(bits_to_bytes(K_ab), bits_to_bytes(K_bc))

    # c reconstructs end-to-end key: K_ac = M XOR K_bc
    K_ac = bytes_to_bits(xor_bytes(M, bits_to_bytes(K_bc)), L)

    # verify: K_ac must equal K_ab (so that A and C share same end-to-end key)
    ok = (K_ac == K_ab)

    print("\n==============================")
    print("3-NODE BB84 (a - b - c)")
    print("==============================")
    print(f"Generated link keys: K_ab({len(get_key_bits(a,'b'))} bits), K_bc({len(get_key_bits(b,'c'))} bits)")
    print(f"Relayed end-to-end key length: {L} bits")
    print(f"A and C share same key via trusted relay at b: {ok}")
    print("\nKey sample (first 64 bits):")
    print("A side:", "".join(map(str, K_ab[:64])))
    print("C side:", "".join(map(str, K_ac[:64])))
    print("==============================\n")


if __name__ == "__main__":
    run_bb84_ab_bc()

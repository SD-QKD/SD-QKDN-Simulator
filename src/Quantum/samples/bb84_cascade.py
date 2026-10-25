import time
import matplotlib.pyplot as plt
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.qkd.cascade import pair_cascade_protocols

# --- Custom Application Layer ---

class KeyManager():
    def __init__(self, timeline, keysize, num_keys):
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []
        
    def send_request(self):
        # We push to the CASCADE protocol (index 1 in the stack)
        for p in self.lower_protocols:
            p.push(self.keysize, self.num_keys)
            
    def pop(self, key):
        # Cascade returns the final corrected key bits
        self.keys.append(key)
        # Record time in milliseconds
        self.times.append(self.timeline.now() * 1e-9)

# --- Simulation Logic ---

def test(sim_time, keysize):
    """
    sim_time: duration of simulation time (ms)
    keysize: size of generated secure key (bits)
    """
    # 1. Initialize Timeline (ms to ps)
    tl = Timeline(sim_time * 1e9)
    
    # 2. Create QKD Nodes
    # Default QKDNode includes the full stack (BB84, Cascade, etc.)
    n1 = QKDNode("n1", tl)
    n2 = QKDNode("n2", tl)
    n1.set_seed(0)
    n2.set_seed(1)
    
    # 3. Pair Protocols
    # Protocol 0 is BB84 (Quantum Level)
    pair_bb84_protocols(n1.protocol_stack[0], n2.protocol_stack[0])
    # Protocol 1 is Cascade (Error Correction Level)
    pair_cascade_protocols(n1.protocol_stack[1], n2.protocol_stack[1])
    
    # 4. Connect Channels
    cc0 = ClassicalChannel("cc_n1_n2", tl, distance=1e3)
    cc1 = ClassicalChannel("cc_n2_n1", tl, distance=1e3)
    cc0.set_ends(n1, n2.name)
    cc1.set_ends(n2, n1.name)
    
    qc0 = QuantumChannel("qc_n1_n2", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc1 = QuantumChannel("qc_n2_n1", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc0.set_ends(n1, n2.name)
    qc1.set_ends(n2, n1.name)
    
    # 5. Setup Key Managers
    # We point the KeyManager to stack index [1] (Cascade)
    km1 = KeyManager(tl, keysize, 10)
    km1.lower_protocols.append(n1.protocol_stack[1])
    n1.protocol_stack[1].upper_protocols.append(km1)
    
    km2 = KeyManager(tl, keysize, 10)
    km2.lower_protocols.append(n2.protocol_stack[1])
    n2.protocol_stack[1].upper_protocols.append(km2)
    
    # 6. Run Simulation
    tl.init()
    km1.send_request()
    
    print(f"Starting BB84 + Cascade simulation...")
    print(f"Parameters: Time={sim_time}ms, KeySize={keysize} bits")
    tick = time.time()
    tl.run()
    print("Execution time %.2f sec" % (time.time() - tick))
    
    # 7. Metrics and Plotting
    if km1.times:
        plt.figure(figsize=(10, 6))
        plt.plot(km1.times, range(1, len(km1.keys) + 1), marker="o")
        plt.xlabel("Simulation time (ms)")
        plt.ylabel("Number of Completed Keys")
        plt.title("Key Generation with Cascade Error Correction")
        plt.grid(True)
        plt.savefig("cascade_throughput.png")
        print("Plot saved as cascade_throughput.png")
    else:
        print("No keys completed. Cascade takes longer than BB84; try increasing sim_time.")

    # 8. Verify Error Correction
    # We compare Alice's keys and Bob's keys bit-by-bit
    print("\nVerifying Key Bit Errors after Cascade:")
    for i in range(min(len(km1.keys), len(km2.keys))):
        key1 = km1.keys[i]
        key2 = km2.keys[i]
        
        # XOR the keys: result is 0 if bits match, 1 if they differ
        diff = key1 ^ key2
        error_count = bin(diff).count('1')
        
        error_percentage = (error_count / keysize) * 100
        print(f"\tKey {i + 1}: {error_count} errors ({error_percentage:.2f}%)")

if __name__ == "__main__":
    # Cascade is computationally expensive.
    # Documentation suggests sim_time=1000 for keysize=512.
    # For a quicker test, we use 100ms and 128 bits.
    test(sim_time=100, keysize=128)
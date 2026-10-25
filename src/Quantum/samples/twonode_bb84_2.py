import time
import matplotlib.pyplot as plt
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import pair_bb84_protocols
from sequence.constants import MILLISECOND

# --- Custom Application Layer ---

class KeyManager():
    """Custom class to interface with the BB84 protocol stack.
    
    This class uses the 'push' and 'pop' mechanism:
    - push: sends a request for keys DOWN to the BB84 protocol.
    - pop: receives the generated keys UP from the BB84 protocol.
    """
    def __init__(self, timeline, keysize, num_keys):
        self.timeline = timeline
        self.lower_protocols = []
        self.keysize = keysize
        self.num_keys = num_keys
        self.keys = []
        self.times = []
        
    def send_request(self):
        # Sends a request to generate keys to the lower protocol (BB84)
        for p in self.lower_protocols:
            p.push(self.keysize, self.num_keys)
            
    def pop(self, info):
        # Callback function for when BB84 finishes a key
        self.keys.append(info)
        # Record the simulation time (converted to milliseconds)
        self.times.append(self.timeline.now() / MILLISECOND)

# --- Simulation Logic ---

def test(sim_time, keysize):
    """
    sim_time: duration of simulation time (ms)
    keysize: size of generated secure key (bits)
    """
    # 1. Initialize Timeline (convert ms input to picoseconds)
    tl = Timeline(sim_time * 1e9)
    
    # 2. Create QKD Nodes
    # stack_size=1 means only the BB84 protocol is loaded into the stack
    n1 = QKDNode("n1", tl, stack_size=1)
    n2 = QKDNode("n2", tl, stack_size=1)
    n1.set_seed(0)
    n2.set_seed(1)
    
    # 3. Pair the protocols (sets up Alice-Bob relationship)
    # n1.protocol_stack[0] is the BB84 protocol instance
    pair_bb84_protocols(n1.protocol_stack[0], n2.protocol_stack[0])
    
    # 4. Connect Classical Channels (Bidirectional)
    cc0 = ClassicalChannel("cc_n1_n2", tl, distance=1e3)
    cc1 = ClassicalChannel("cc_n2_n1", tl, distance=1e3)
    cc0.set_ends(n1, n2.name)
    cc1.set_ends(n2, n1.name)
    
    # 5. Connect Quantum Channels (Bidirectional)
    # Polarization fidelity of 0.97 introduces bit errors
    qc0 = QuantumChannel("qc_n1_n2", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc1 = QuantumChannel("qc_n2_n1", tl, attenuation=1e-5, distance=1e3, polarization_fidelity=0.97)
    qc0.set_ends(n1, n2.name)
    qc1.set_ends(n2, n1.name)
    
    # 6. Instantiate custom KeyManagers and link to the Protocol Stack
    # We request 25 keys total
    km1 = KeyManager(tl, keysize, 1)
    km1.lower_protocols.append(n1.protocol_stack[0])
    n1.protocol_stack[0].upper_protocols.append(km1)
    
    km2 = KeyManager(tl, keysize, 1)
    km2.lower_protocols.append(n2.protocol_stack[0])
    n2.protocol_stack[0].upper_protocols.append(km2)
    
    # 7. Initialize and Run Simulation
    tl.init()
    km1.send_request() # Trigger the first request
    
    print(f"Starting BB84 simulation: {sim_time}ms, Keysize: {keysize} bits...")
    tick = time.time()
    tl.run()
    print("Execution time %.2f sec" % (time.time() - tick))
    
    # 8. Display Metrics
    if km1.times:
        plt.figure(figsize=(10, 6))
        plt.plot(km1.times, range(1, len(km1.keys) + 1), marker="o")
        print("\nAlice (n1) key:")
        print(n1.protocol_stack[0].key)

        print("\nBob (n2) key:")
        print(n2.protocol_stack[0].key)
        plt.xlabel("Simulation time (ms)")
        plt.ylabel("Number of Completed Keys")
        plt.title("Key Generation Throughput")
        plt.grid(True)
        plt.savefig("bb84_throughput.png")
        print("Plot saved as bb84_throughput.png")
    else:
        print("No keys completed within the simulation time.")
    
    # 9. Print Error Rates
    print("\nKey Error Rates (QBER):")
    # Access the error rates tracked by the BB84 protocol instance
    for i, e in enumerate(n1.protocol_stack[0].error_rates):
        print("\tKey {}:\t{:.2f}%".format(i + 1, e * 100))

# --- Execution ---

if __name__ == "__main__":
    # Parameters from the documentation interact widget
    # sim_time: 10 ms
    # keysize: 256 bits
    test(sim_time=10, keysize=256)
import time
import matplotlib.pyplot as plt
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QKDNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.qkd.BB84 import BB84, pair_bb84_protocols
from sequence.constants import MILLISECOND

def test_bb84(sim_time, cc_delay, qc_atten, qc_dist, key_length=256, key_num=10):
    """
    Three-node BB84 simulation with trusted relay architecture.
    
    Args:
        sim_time: duration of simulation time (ms)
        cc_delay: delay on classical channels (ms)
        qc_atten: attenuation on quantum channels (dB/m)
        qc_dist: distance of quantum channels (km)
        key_length: length of each key to generate (bits)
        key_num: number of keys to generate per link
    """
    
    PS_PER_MS = 1e9
    M_PER_KM = 1e3
    
    # Convert units
    cc_delay_ps = cc_delay * PS_PER_MS
    qc_dist_m = qc_dist * M_PER_KM
    
    # 1. Construct the simulation timeline
    tl = Timeline(sim_time * PS_PER_MS)
    
    # 2. Construct QKD nodes
    node1 = QKDNode("node1", tl)
    node2 = QKDNode("node2", tl)  # This will be the trusted relay
    node3 = QKDNode("node3", tl)
    
    nodes = [node1, node2, node3]
    
    # Debug: Print available components
    print("Available components in node1:")
    for comp_name, comp in node1.components.items():
        print(f"  - {comp_name}: {type(comp).__name__}")
    
    # 3. Set seeds for reproducibility
    for i, node in enumerate(nodes):
        node.set_seed(i)
    
    # 4. Create all-to-all classical channels
    for n1 in nodes:
        for n2 in nodes:
            if n1 == n2:
                continue
            cc = ClassicalChannel(f"cc_{n1.name}_{n2.name}", tl, 1e3, delay=cc_delay_ps)
            cc.set_ends(n1, n2.name)
    
    # 5. Create quantum channels
    # Link node1 to node2
    qc_1_2 = QuantumChannel("qc_node1_node2", tl, qc_atten, qc_dist_m)
    qc_1_2.set_ends(node1, node2.name)
    
    # Link node2 to node3
    qc_2_3 = QuantumChannel("qc_node2_node3", tl, qc_atten, qc_dist_m)
    qc_2_3.set_ends(node2, node3.name)
    
    # 6. Find the correct component names
    # Look for lightsource and detector components
    def find_component_by_type(node, component_type_name):
        """Find component by type name"""
        for name, comp in node.components.items():
            if component_type_name.lower() in type(comp).__name__.lower():
                return name
        return None
    
    # Try to find lightsource and detector names
    ls_name_1 = find_component_by_type(node1, "light")
    qsd_name_1 = find_component_by_type(node1, "detector")
    
    ls_name_2 = find_component_by_type(node2, "light")
    qsd_name_2 = find_component_by_type(node2, "detector")
    
    ls_name_3 = find_component_by_type(node3, "light")
    qsd_name_3 = find_component_by_type(node3, "detector")
    
    print(f"\nFound components:")
    print(f"  node1: lightsource={ls_name_1}, detector={qsd_name_1}")
    print(f"  node2: lightsource={ls_name_2}, detector={qsd_name_2}")
    print(f"  node3: lightsource={ls_name_3}, detector={qsd_name_3}")
    
    if not all([ls_name_1, qsd_name_1, ls_name_2, qsd_name_2, ls_name_3, qsd_name_3]):
        print("\nERROR: Could not find required components!")
        print("QKDNode might not have the required hardware initialized.")
        print("\nTrying alternative approach with component list:")
        
        # Print all components to help debug
        for node in nodes:
            print(f"\n{node.name} components:")
            for name, comp in node.components.items():
                print(f"  {name}: {type(comp)}")
        
        raise ValueError("Required BB84 hardware components not found. Check QKDNode initialization.")
    
    # 7. Create and pair BB84 protocol instances
    
    # Link 1: node1 (Alice) <-> node2 (Bob)
    bb84_node1_to_node2 = BB84(node1, "bb84_1_2_alice", ls_name_1, qsd_name_1)
    bb84_node2_from_node1 = BB84(node2, "bb84_1_2_bob", ls_name_2, qsd_name_2)
    
    # Pair the protocols
    pair_bb84_protocols(bb84_node1_to_node2, bb84_node2_from_node1)
    
    # Add protocols to node protocol stacks
    node1.protocol_stack[0] = bb84_node1_to_node2
    node2.protocol_stack[0] = bb84_node2_from_node1
    
    # Link 2: node2 (Alice) <-> node3 (Bob)
    # Note: node2 needs a second protocol instance for the second link
    # We'll use protocol_stack[1] for the second link
    bb84_node2_to_node3 = BB84(node2, "bb84_2_3_alice", ls_name_2, qsd_name_2)
    bb84_node3_from_node2 = BB84(node3, "bb84_2_3_bob", ls_name_3, qsd_name_3)
    
    # Pair the protocols
    pair_bb84_protocols(bb84_node2_to_node3, bb84_node3_from_node2)
    
    # Add protocols to protocol stacks
    # For node2, we need to handle having two BB84 instances
    if len(node2.protocol_stack) > 1:
        node2.protocol_stack[1] = bb84_node2_to_node3
    else:
        node2.protocol_stack.append(bb84_node2_to_node3)
    
    node3.protocol_stack[0] = bb84_node3_from_node2
    
    # 8. Initialize timeline
    tl.init()
    
    # 9. Start key generation
    print(f"\nStarting BB84 3-node simulation: {sim_time}ms, {qc_dist}km distance per link...")
    print(f"Generating {key_num} keys of length {key_length} bits on each link")
    
    # Start key generation on both links
    # Link 1: node1 -> node2
    bb84_node1_to_node2.push(key_length, key_num, run_time=sim_time * PS_PER_MS)
    
    # Link 2: node2 -> node3 (can run in parallel or sequentially)
    bb84_node2_to_node3.push(key_length, key_num, run_time=sim_time * PS_PER_MS)
    
    # Run simulation
    tick = time.time()
    tl.run()
    print("Execution time %.2f sec" % (time.time() - tick))
    
    # 10. Collect and display results
    print("\n" + "="*60)
    print("BB84 SIMULATION RESULTS")
    print("="*60)
    
    # Link 1 Results
    print("\n--- Link 1: node1 ↔ node2 ---")
    print(f"Keys generated (node1): {len(bb84_node1_to_node2.throughputs)}")
    print(f"Keys generated (node2): {len(bb84_node2_from_node1.throughputs)}")
    if bb84_node1_to_node2.throughputs:
        print(f"Average throughput: {sum(bb84_node1_to_node2.throughputs)/len(bb84_node1_to_node2.throughputs):.2f} bits/s")
        print(f"Latency: {bb84_node1_to_node2.latency:.6f} s")
    if bb84_node1_to_node2.error_rates:
        avg_qber = sum(bb84_node1_to_node2.error_rates) / len(bb84_node1_to_node2.error_rates)
        print(f"Average QBER: {avg_qber:.6f}")
    
    # Link 2 Results
    print("\n--- Link 2: node2 ↔ node3 ---")
    print(f"Keys generated (node2): {len(bb84_node2_to_node3.throughputs)}")
    print(f"Keys generated (node3): {len(bb84_node3_from_node2.throughputs)}")
    if bb84_node2_to_node3.throughputs:
        print(f"Average throughput: {sum(bb84_node2_to_node3.throughputs)/len(bb84_node2_to_node3.throughputs):.2f} bits/s")
        print(f"Latency: {bb84_node2_to_node3.latency:.6f} s")
    if bb84_node2_to_node3.error_rates:
        avg_qber = sum(bb84_node2_to_node3.error_rates) / len(bb84_node2_to_node3.error_rates)
        print(f"Average QBER: {avg_qber:.6f}")
    
    # 11. Generate plots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))
    
    # Plot 1: Throughput over time - Link 1
    if bb84_node1_to_node2.throughputs:
        ax1.plot(range(1, len(bb84_node1_to_node2.throughputs) + 1), 
                bb84_node1_to_node2.throughputs, 
                marker='o', color='blue', label='Link 1 (node1↔node2)')
        ax1.set_title("BB84 Throughput - Link 1")
        ax1.set_xlabel("Key Number")
        ax1.set_ylabel("Throughput (bits/s)")
        ax1.grid(True, alpha=0.3)
        ax1.legend()
    
    # Plot 2: Throughput over time - Link 2
    if bb84_node2_to_node3.throughputs:
        ax2.plot(range(1, len(bb84_node2_to_node3.throughputs) + 1), 
                bb84_node2_to_node3.throughputs, 
                marker='s', color='green', label='Link 2 (node2↔node3)')
        ax2.set_title("BB84 Throughput - Link 2")
        ax2.set_xlabel("Key Number")
        ax2.set_ylabel("Throughput (bits/s)")
        ax2.grid(True, alpha=0.3)
        ax2.legend()
    
    # Plot 3: QBER - Link 1
    if bb84_node1_to_node2.error_rates:
        ax3.plot(range(1, len(bb84_node1_to_node2.error_rates) + 1), 
                bb84_node1_to_node2.error_rates, 
                marker='o', color='red', label='Link 1')
        ax3.set_title("Quantum Bit Error Rate (QBER) - Link 1")
        ax3.set_xlabel("Key Number")
        ax3.set_ylabel("QBER")
        ax3.grid(True, alpha=0.3)
        ax3.legend()
    
    # Plot 4: QBER - Link 2
    if bb84_node2_to_node3.error_rates:
        ax4.plot(range(1, len(bb84_node2_to_node3.error_rates) + 1), 
                bb84_node2_to_node3.error_rates, 
                marker='s', color='orange', label='Link 2')
        ax4.set_title("Quantum Bit Error Rate (QBER) - Link 2")
        ax4.set_xlabel("Key Number")
        ax4.set_ylabel("QBER")
        ax4.grid(True, alpha=0.3)
        ax4.legend()
    
    fig.tight_layout()
    plt.savefig("bb84_results.png", dpi=150)
    print("\nSaved: bb84_results.png")
    plt.show()
    
    # Return protocol instances for further analysis if needed
    return {
        'link1_alice': bb84_node1_to_node2,
        'link1_bob': bb84_node2_from_node1,
        'link2_alice': bb84_node2_to_node3,
        'link2_bob': bb84_node3_from_node2
    }


# --- Run the script ---
if __name__ == "__main__":
    # Parameters optimized for BB84:
    # sim_time: 5000ms (BB84 needs more time than entanglement generation)
    # cc_delay: 0.01ms (faster classical communication)
    # qc_atten: 1e-5 dB/m (low attenuation for testing)
    # qc_dist: 1km per hop (shorter distance for faster simulation)
    # key_length: 128 bits per key (shorter keys generate faster)
    # key_num: 2 keys per link (just two keys to verify it works)
    protocols = test_bb84(
        sim_time=5000,      # Increased simulation time
        cc_delay=0.01,      # Faster classical channels
        qc_atten=1e-5, 
        qc_dist=1,          # Reduced distance to 1km
        key_length=128,     # Shorter key length
        key_num=2           # Just 2 keys to test
    )
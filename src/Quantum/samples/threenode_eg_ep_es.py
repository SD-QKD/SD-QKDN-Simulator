import time
import matplotlib.pyplot as plt
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QuantumRouter, BSMNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.constants import MILLISECOND


RAW_FIDELITY = 0.95
REQUEST_FIDELITY = 0.8

def test(sim_time, cc_delay, qc_atten, qc_dist):
    """
    sim_time: duration of simulation time (ms)
    cc_delay: delay on classical channels (ms)
    qc_atten: attenuation on quantum channels (dB/m)
    qc_dist: distance of quantum channels (km)
    """
    
    PS_PER_MS = 1e9
    M_PER_KM = 1e3
    
    # Convert units
    cc_delay_ps = cc_delay * PS_PER_MS
    qc_dist_m = qc_dist * M_PER_KM
    
    # Construct the simulation timeline
    tl = Timeline(sim_time * PS_PER_MS)
    
    # Construct the quantum routers
    r1 = QuantumRouter("r1", tl, 50)
    r2 = QuantumRouter("r2", tl, 100)
    r3 = QuantumRouter("r3", tl, 50)
    
    # BSM nodes (Middle nodes for entanglement swapping)
    m1 = BSMNode("m1", tl, ["r1", "r2"])
    m2 = BSMNode("m2", tl, ["r2", "r3"])
    
    # Set up node relationships
    r1.add_bsm_node(m1.name, r2.name)
    r2.add_bsm_node(m1.name, r1.name)
    r2.add_bsm_node(m2.name, r3.name)
    r3.add_bsm_node(m2.name, r2.name)
    
    # Seeds for reproducibility
    nodes = [r1, r2, r3, m1, m2]
    for i, node in enumerate(nodes):
        node.set_seed(i)
    
    # Configure Memory Parameters
    for node in [r1, r2, r3]:
        memory_array = node.get_components_by_type("MemoryArray")[0]
        memory_array.update_memory_params("coherence_time", 10) 
        memory_array.update_memory_params("raw_fidelity", RAW_FIDELITY)
    
    # Al-to-all classical connections
    for node1 in nodes:
        for node2 in nodes:
            if node1 == node2:
                continue
            cc = ClassicalChannel(f"cc_{node1.name}_{node2.name}", tl, 1e3, delay=cc_delay_ps)
            cc.set_ends(node1, node2.name)
            
    #Create quantum channels
    # Link r1 and r2 to m1
    qc0 = QuantumChannel("qc_r1_m1", tl, qc_atten, qc_dist_m)
    qc1 = QuantumChannel("qc_r2_m1", tl, qc_atten, qc_dist_m)
    qc0.set_ends(r1, m1.name)
    qc1.set_ends(r2, m1.name)
    
    # Link r2 and r3 to m2
    qc2 = QuantumChannel("qc_r2_m2", tl, qc_atten, qc_dist_m)
    qc3 = QuantumChannel("qc_r3_m2", tl, qc_atten, qc_dist_m)
    qc2.set_ends(r2, m2.name)
    qc3.set_ends(r3, m2.name)

    # Create routing table (Forwarding rules for the network manager)
    # r1 -> r3 goes through r2
    r1.network_manager.protocol_stack[0].add_forwarding_rule("r2", "r2")
    r1.network_manager.protocol_stack[0].add_forwarding_rule("r3", "r2")
    
    r2.network_manager.protocol_stack[0].add_forwarding_rule("r1", "r1")
    r2.network_manager.protocol_stack[0].add_forwarding_rule("r3", "r3")
    
    r3.network_manager.protocol_stack[0].add_forwarding_rule("r1", "r2")
    r3.network_manager.protocol_stack[0].add_forwarding_rule("r2", "r2")
    
    # Initialize and Request Entanglement
    tl.init()
    # Request: r1 to r3, start at 0.1s, end at 10s, 50 memories, target fidelity 0.8
    r1.network_manager.request("r3", 0.1e12, 10e12, 50, REQUEST_FIDELITY)

    print(f"Starting 3-node simulation: {sim_time}ms, {qc_dist}km distance...")
    tick = time.time()
    tl.run()
    print("Execution time %.2f sec" % (time.time() - tick))
    
    # --- PLOTTING 1: Entanglement Over Time ---
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(10, 5)

    # Router 1 Data
    data1 = [info.entangle_time / MILLISECOND for info in r1.resource_manager.memory_manager if info.entangle_time > 0]
    data1.sort()
    ax1.plot(data1, range(1, len(data1) + 1), marker="o", color='blue')
    ax1.set_title("Router r1: Entanglement Success")
    ax1.set_ylabel("Number of Entangled Memories")
    ax1.set_xlabel("Simulation Time (ms)")
    
    # Router 3 Data
    data3 = [info.entangle_time / MILLISECOND for info in r3.resource_manager.memory_manager if info.entangle_time > 0]
    data3.sort()
    ax2.plot(data3, range(1, len(data3) + 1), marker="o", color='green')
    ax2.set_title("Router r3: Entanglement Success")
    ax2.set_xlabel("Simulation Time (ms)")
    
    fig.tight_layout()
    plt.savefig("entanglement_time_plot.png")
    print("Saved: entanglement_time_plot.png")

    # --- PLOTTING 2: Fidelity Metrics ---
    fig, (ax1, ax2) = plt.subplots(1, 2)
    fig.set_size_inches(10, 5)
    
    # Fidelity r1
    fid_data1 = [info.fidelity for info in r1.resource_manager.memory_manager]
    ax1.bar(range(len(fid_data1)), fid_data1, color='skyblue')
    ax1.plot([0, len(fid_data1)], [RAW_FIDELITY, RAW_FIDELITY], "--", label="Raw Fid")
    ax1.plot([0, len(fid_data1)], [REQUEST_FIDELITY, REQUEST_FIDELITY], "--", color='red', label="Req Fid")
    ax1.set_ylim(0.7, 1.0)
    ax1.set_title("r1 Memory Fidelity")
    ax1.set_ylabel("Fidelity")
    ax1.set_xlabel("Memory Index")

    # Fidelity r3
    fid_data3 = [info.fidelity for info in r3.resource_manager.memory_manager]
    ax2.bar(range(len(fid_data3)), fid_data3, color='lightgreen')
    ax2.plot([0, len(fid_data3)], [RAW_FIDELITY, RAW_FIDELITY], "--")
    ax2.plot([0, len(fid_data3)], [REQUEST_FIDELITY, REQUEST_FIDELITY], "--", color='red')
    ax2.set_ylim(0.7, 1.0)
    ax2.set_title("r3 Memory Fidelity")
    ax2.set_xlabel("Memory Index")
    
    fig.tight_layout()
    plt.savefig("fidelity_plot.png")
    print("Saved: fidelity_plot.png")
    
    plt.show()

    # print("\n=== ENTANGLEMENT CHECK: r1 ↔ r3 ===")

    # entangled_pairs = 0

    # for info in r1.resource_manager.memory_manager:
    #     if (
    #         info.state == "ENTANGLED" and
    #         info.remote_node == "r3"
    #     ):
    #         entangled_pairs += 1
    #         print(
    #             f"Memory {info.index} | "
    #             f"Partner: {info.remote_node} | "
    #             f"Fidelity: {info.fidelity:.4f} | "
    #             f"Time: {info.entangle_time / MILLISECOND:.2f} ms"
    #         )

    # print(f"\nTotal r1–r3 entangled memories: {entangled_pairs}")


# --- Run the script with specific parameters ---
if __name__ == "__main__":
    # Parameters:
    # sim_time: 200ms
    # cc_delay: 0.1ms
    # qc_atten: 1e-5 dB/m (standard is ~2e-4 for 0.2dB/km)
    # qc_dist: 5km per hop (Total distance r1 to r3 is 20km)
    test(sim_time=200, cc_delay=0.1, qc_atten=1e-5, qc_dist=5)
import time
import matplotlib.pyplot as plt
from sequence.kernel.timeline import Timeline
from sequence.topology.node import QuantumRouter, BSMNode
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.resource_management.rule_manager import Rule
from sequence.entanglement_management.generation import EntanglementGenerationA
from sequence.constants import MILLISECOND

# --- Rule Definition Functions ---

# our rule condition requires RAW (unentangled) memories
def eg_rule_condition(memory_info, manager, args):
    if memory_info.state == "RAW":
        return [memory_info]
    else:
        return []

# define action to be taken when we meet our condition on router 1
def eg_rule_action1(memories_info, args):
    # define requirement of protocols on other node
    def eg_req_func(protocols, args):
        for protocol in protocols:
            if isinstance(protocol, EntanglementGenerationA):
                return protocol
            
    # create entanglement generation protocol with proper parameters
    memories = [info.memory for info in memories_info]
    memory = memories[0]
    protocol = EntanglementGenerationA.create(None, "EGA." + memory.name, "m1", "r2", memory)
    protocol.primary = True
    
    # return values for a rule are: the protocol created, the destination node,
    # the destination condition, and arguments for the condition.
    return [protocol, ["r2"], [eg_req_func], [None]]

# define action to be taken when we meet our condition on router 2
def eg_rule_action2(memories_info, args):
    memories = [info.memory for info in memories_info]
    memory = memories[0]
    protocol = EntanglementGenerationA.create(None, "EGA." + memory.name, "m1", "r1", memory)
    return [protocol, [None], [None], [None]]


# --- Main Simulation Function ---

def test(sim_time, cc_delay, qc_atten, qc_dist):
    """
    sim_time: duration of simulation time (ms)
    cc_delay: delay on classical channels (ms)
    qc_atten: attenuation on quantum channels (db/m)
    qc_dist: distance of quantum channels (km)
    """
    
    PS_PER_MS = 1e9
    M_PER_KM = 1e3
    
    # convert units for cc delay (to ps) and qc distance (to m)
    cc_delay *= PS_PER_MS
    qc_dist *= M_PER_KM
    
    # construct the simulation timeline; the constructor argument is the simulation time (in ps)
    tl = Timeline(sim_time * PS_PER_MS)
    
    # first, construct the quantum routers
    r1 = QuantumRouter("r1", tl, 50) # each node has 50 memories
    r2 = QuantumRouter("r2", tl, 50)
    
    # next, construct the BSM nodes
    m1 = BSMNode("m1", tl, ["r1", "r2"])
    
    r1.set_seed(0)
    r2.set_seed(1)
    m1.set_seed(2)
    
    # Optional: update coherence time if needed
    for node in [r1, r2]:
        memory_array = node.get_components_by_type("MemoryArray")[0]
        # memory_array.update_memory_params("coherence_time", 0.3)
    
    # create all-to-all classical connections
    nodes = [r1, r2, m1]
    for node1 in nodes:
        for node2 in nodes:
            if node1 == node2:
                continue
            cc = ClassicalChannel("_".join(["cc", node1.name, node2.name]), tl, 1e3, delay=cc_delay)
            cc.set_ends(node1, node2.name)
    
    # create linear quantum network between routers and middle node
    qc1 = QuantumChannel("qc_r1_m1", tl, qc_atten, qc_dist)
    qc1.set_ends(r1, m1.name)
    qc2 = QuantumChannel("qc_r2_m1", tl, qc_atten, qc_dist)
    qc2.set_ends(r2, m1.name)
    
    # initialize our simulation kernel and instantiate the written rules
    tl.init()
    rule1 = Rule(10, eg_rule_action1, eg_rule_condition, None, None)
    r1.resource_manager.load(rule1)
    rule2 = Rule(10, eg_rule_action2, eg_rule_condition, None, None)
    r2.resource_manager.load(rule2)
    
    print(f"Starting simulation for {sim_time} ms...")
    tick = time.time()
    tl.run()
    print("Execution time %.2f sec" % (time.time() - tick))
    
    # display our collected metrics
    data = []
    for info in r1.resource_manager.memory_manager:
        if info.entangle_time > 0:
            data.append(info.entangle_time / MILLISECOND)
    data.sort()
    
    if data:
        plt.figure(figsize=(10, 6))
        plt.plot(data, range(1, len(data) + 1), marker="o")
        plt.xlabel("Simulation Time (ms)")
        plt.ylabel("Aggregated Number of Entangled Memory")
        plt.title("Entanglement Generation Success Over Time")
        plt.grid(True)
        plt.savefig("entanglement_plot.png") 
        print("Plot saved as entanglement_plot.png")
        print(f'Entangled time data (ms): {data}')
    else:
        print("No entanglement events recorded. Check attenuation or simulation time.")

# --- Execution Block ---

if __name__ == "__main__":
    # Example parameters:
    # sim_time: 100 ms
    # cc_delay: 0.1 ms
    # qc_atten: 1e-5 dB/m (very low for demo)
    # qc_dist: 20 km
    test(sim_time=100, cc_delay=0.1, qc_atten=1e-5, qc_dist=20)
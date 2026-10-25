import logging
logging.basicConfig(level=logging.DEBUG)
from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node
from sequence.components.optical_channel import QuantumChannel, ClassicalChannel
from sequence.message import Message

# 1. Setup Timeline
tl = Timeline()

# 2. Create 20 Nodes
nodes = [Node(f"Node_{i}", tl) for i in range(20)]

# 3. Connect in a line
for i in range(19):
    # Standard attenuation for fiber (~0.2 dB/km -> 0.0002 dB/m)
    qc = QuantumChannel(f"QC_{i}", tl, distance=1000, attenuation=0.0002)
    qc.set_ends(nodes[i], nodes[i+1].name)
    
    cc = ClassicalChannel(f"CC_{i}", tl, distance=1000)
    cc.set_ends(nodes[i], nodes[i+1].name)
    
    # Map the classical channel so the sender can find the path to its neighbor
    nodes[i].cchannels[nodes[i+1].name] = cc

# 4. Define Receiver Logic
def custom_receive_message(self, src: str, msg: "Message"):
    print(f"\nSUCCESS: {self.name} received message '{msg.msg_type}' from {src} at {self.timeline.now()} ps")

# Attach the receiver logic to Node_1
nodes[1].receive_message = custom_receive_message.__get__(nodes[1], Node)

# 5. Define and Schedule the Event
def test_simulation():
    msg = Message(msg_type="PING_TEST", receiver="Node_1")
    # Corrected: transmit(message, sender_object, propagation_delay)
    # nodes[0] is the sender, so it must be passed here
    nodes[0].cchannels["Node_1"].transmit(msg, nodes[0], 0)
    print(f">>> {nodes[0].name} initiated transmission at time {tl.now()}")

# 6. Initialize and Run
test_simulation()
tl.init()
tl.run()

print(f"Simulation ended at time: {tl.now()} ps")
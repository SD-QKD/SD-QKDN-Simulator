from sequence.kernel.timeline import Timeline
from sequence.topology.node import Node
from sequence.components.memory import Memory
from sequence.components.detector import Detector
from sequence.components.optical_channel import QuantumChannel
from sequence.kernel.process import Process
from sequence.kernel.event import Event
        

class SenderNode(Node):
    def __init__(self, name, timeline):
        super().__init__(name, timeline)
        
        memory_name = name + ".memory"
        memory = Memory(memory_name, timeline, fidelity=1, frequency=0,
                        efficiency=1, coherence_time=0, wavelength=500)
        self.add_component(memory)
        memory.add_receiver(self)

    def get(self, photon, **kwargs):
        self.send_qubit(kwargs['dst'], photon)

class Counter:
    def __init__(self):
        self.count = 0
        self.time = 0

    def trigger(self, detector, info):
        self.count += 1
        self.time = info['time']

class ReceiverNode(Node):
    def __init__(self, name, timeline):
        super().__init__(name, timeline)

        detector_name = name + ".detector"
        detector = Detector(detector_name, timeline, efficiency=1)
        self.add_component(detector)
        self.set_first_component(detector_name)
        detector.owner = self

        self.counter = Counter()
        detector.attach(self.counter)

    def receive_qubit(self, src, qubit):
        self.components[self.first_component_name].get(qubit)

tl = Timeline(10e12) # ps

alice = SenderNode("Alice", tl)
bob = ReceiverNode("Bob", tl)
alice.set_seed(0)
bob.set_seed(1)

qc = QuantumChannel("qc", tl, attenuation=0, distance=1e3)
qc.set_ends(alice, bob.name)

memories = alice.get_components_by_type(Memory)
memory = memories[0]
memory.update_state([complex(0), complex(1)]) # down state (only state when photon is excited)
# memory.update_state([complex(0), complex(0)]) # up state (photon never emitted)
process = Process(memory, "excite", ["Bob"])
event = Event(0, process)
tl.schedule(event)

tl.init()
tl.run()

print("detection count: {}".format(bob.counter.count))
print("detection time: {}".format(bob.counter.time))
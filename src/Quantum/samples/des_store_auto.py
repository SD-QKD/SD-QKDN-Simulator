from sequence.kernel.timeline import Timeline
from sequence.kernel.event import Event
from sequence.kernel.process import Process

class Store(object):
    def __init__(self, tl: Timeline):
        self.opening = False
        self.timeline = tl

    def open(self) -> None:
        if self.timeline.now() >= 60:
            self.timeline.stop()
        self.opening = True
        process = Process(self, 'close', [])
        event = Event(self.timeline.now() + 12, process)
        self.timeline.schedule(event)

    def close(self) -> None:
        if self.timeline.now() >= 60:
            self.timeline.stop()
        self.opening = False
        process = Process(self, 'open', [])
        event = Event(self.timeline.now() + 12, process)
        self.timeline.schedule(event)

# tl = Timeline()   # if you use tl.run(), simulation will get stuck in an infinite loop
tl = Timeline(60) # simulate system for 60 hours
tl.show_progress = False
store = Store(tl)
process = Process(store, 'open', [])
event = Event(7, process) # occuring at 7:00 
tl.schedule(event)

for t in [15, 32, 52, 55, 56]:
    tl = Timeline(t)
    store = Store(tl)
    
    process = Process(store, 'open', [])
    event = Event(7, process)
    tl.schedule(event)
    
    tl.run()
    print(tl.now())
    print(f"{t} : {(store.opening)}")

# True, True, False, False, True
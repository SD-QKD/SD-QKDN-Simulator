# Whether the store is open or closed

from sequence.kernel.timeline import Timeline
from sequence.kernel.event import Event
from sequence.kernel.process import Process

# Create Store class
class Store(object):
    def __init__(self, tl: Timeline):
        self.opening = False
        self.timeline = tl

    def open(self) -> None:
        self.opening = True

    def close(self) -> None:
        self.opening = False


tl = Timeline() # create timeline
tl.show_progress = False # turn off progress bar, we will address this in later tutorials.
store = Store(tl) # create store

# Open store at 7:00
open_proc = Process(store, 'open', []) # Process(object, function name: string, arguments of function: List[])
open_event = Event(7, open_proc) # Event(occurring time: int, process: Process)
tl.schedule(open_event) # Timeline.schedule(Event)

# Open check
print(store.opening) # False
# After aligning with the timeline
tl.run()
print(tl.now(), store.opening) # 7 True

# Close check
close_proc = Process(store, 'close', [])
close_event = Event(19, close_proc)
tl.schedule(close_event)
print(store.opening) # checking before aligning with timeline
tl.run()
print(tl.time, store.opening) # 19 False




# Changing the schedule of close_event and open_event

# open_event -> close_event
tl.time = 0
tl.schedule(open_event)
tl.schedule(close_event)
tl.run()
print(tl.time, store.opening)

# close_event -> open_event
tl.time = 0
tl.schedule(close_event)
tl.schedule(open_event)
tl.run()
print(tl.time, store.opening)

# Both will work the same, because the order of executing events doesnot rely on the order of calling the scheduling method

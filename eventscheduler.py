from sched import scheduler
from time import monotonic, sleep
from threading import Event, Thread

class EventScheduler(object):

    def __init__(self):
        self.scheduler = scheduler(monotonic, sleep)
        self.wake_handle = Event()
        self.thread = Thread(target=self.loop, args=())
        self.running = False

    def schedule(self, delay, action, argument=(), kwargs={}):
        self.scheduler.enter(delay, 1, action, argument, kwargs)
        self.wake_handle.set()

    def loop(self):
        while self.running:
            self.scheduler.run()
            self.wake_handle.wait()
            self.wake_handle.clear()
    
    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.wake_handle.set()

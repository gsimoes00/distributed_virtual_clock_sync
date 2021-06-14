from threading import Lock, Thread
from queue import Empty, Queue
from random import lognormvariate

class QueueChannel(object):
            
    def __init__(self, id, receive_queue, send_receive_queue):
        self.receive_queue = receive_queue
        self.send_queue = send_receive_queue
        self.id = id

    def send(self, message):
        self.send_queue.put(message)

    def receive(self, timeout_ms=None):
        try:
            if timeout_ms:
                timeout_ms /= 1000
            message = self.receive_queue.get(timeout=timeout_ms)
        except Empty:
            message = None
        return message

class QueueCommunication(object):
    
    def __init__(self, scheduler):
        self.node_queues = dict()
        self.last_node_id = 0
        self.node_creation_lock = Lock()
        self.queue_in = Queue()
        self.scheduler = scheduler
        self.thread = Thread(target=self.loop, args=())
        self.running = False

    def register(self):
        node_queue_in = Queue()
        self.node_creation_lock.acquire()
        self.last_node_id += 1
        id = self.last_node_id
        self.node_queues[self.last_node_id] = node_queue_in
        self.node_creation_lock.release()

        node_channel = QueueChannel(id, node_queue_in, self.queue_in)

        return node_channel

    def loop(self):
        while self.running:
            message = self.queue_in.get()
            if message:
                if not message.destination:
                    message.destination = filter(lambda x: x != message.source, self.node_queues.keys()) #exclude sender
                    #message.destination = self.node_queues.keys() #include sender
                for dest in message.destination:
                    delay = (5+lognormvariate(0.8, 0.5))
                    #treat case where destination does not exist
                    try:
                        self.scheduler.schedule_ms(delay, self.node_queues[dest].put, argument=(message,)) #with delay
                        #self.node_queues[dest].put(message) #without delay
                    except KeyError:
                        pass

    def start(self):
        self.running = True
        self.thread.start()

    def stop(self):
        self.running = False
        self.queue_in.put(None)

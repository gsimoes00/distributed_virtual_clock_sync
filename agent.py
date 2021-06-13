import sched
from message import Message
from driftingclock import DriftingClock
from message import Message

class Agent(object):
    
    def __init__(self, channel, scheduler, magnitude=10**(-3), drift=None):
        
        self.clock = DriftingClock(magnitude, drift)
        self.channel = channel
        self.scheduler = scheduler

    def ring_formation(self):

        received_ping = False
        received_ack = False
        next_in_ring = None

        self.channel.send(Message(self.channel.id, [self.channel.id+1], self.clock.get_time(), 'ping', 0))

        while not (received_ping and received_ack):
            message = self.channel.receive(100)
            if message:
                if message.message_type == 'ping' and message.content == 0:
                    received_ping = True
                    self.channel.send(Message(self.channel.id, [message.source], self.clock.get_time(), 'ping', 1))
                elif message.message_type == 'ping' and message.content == 1:
                    received_ack = True
                    next_in_ring = message.source
            else:
                self.channel.send(Message(self.channel.id, [1], self.clock.get_time(), 'ping', 0))
        
        print('Agent %d is part of the ring with %d as its successor.' % (self.channel.id, next_in_ring))
        return next_in_ring


    def start(self):

        self.clock.ntp_sync()
        print('Agent %d synchronized with NTP: %s.' % (self.channel.id, DriftingClock.format_time(self.clock.get_time())))

        next_in_ring = self.ring_formation()
        if next_in_ring == 1:
            print('Agent %d will propose to be master.' % self.channel.id)

        
from message import Message
from driftingclock import DriftingClock
from message import Message
from random import random

class Agent(object):
    
    def __init__(self, channel, scheduler, magnitude=10**(-3), drift=None):
        
        self.clock = DriftingClock(magnitude, drift)
        self.channel = channel
        self.scheduler = scheduler
        self.next_in_ring = None
        self.ring_size = None
        self.participant = False
        self.elected = None

    def ring_formation(self):

        received_ping = False
        received_ack = False

        self.channel.send(Message(self.channel.id, [self.channel.id+1], self.clock.get_time(), 'ping', 0))

        while not (received_ping and received_ack):
            message = self.channel.receive(100)
            if message:
                if message.message_type == 'ping' and message.content == 0:
                    received_ping = True
                    self.channel.send(Message(self.channel.id, [message.source], self.clock.get_time(), 'ping', 1))
                elif message.message_type == 'ping' and message.content == 1:
                    received_ack = True
                    self.next_in_ring = message.source
            else:
                self.channel.send(Message(self.channel.id, [1], self.clock.get_time(), 'ping', 0))
        
        print('Agent %d is part of the ring with %d as its successor.' % (self.channel.id, self.next_in_ring))

        if self.next_in_ring == 1:
            print('Agent %d is broadcasting the size of the ring: %d.' % (self.channel.id, self.channel.id))
            self.channel.send(Message(self.channel.id, [], self.clock.get_time(), 'ring_size', self.channel.id))
            self.ring_size = self.channel.id
        else:
            while not self.ring_size:
                message = self.channel.receive()
                if message.message_type == 'ring_size':
                    self.ring_size = message.content

    def ring_election(self):

        chance_to_propose = 1/((self.ring_size)*(self.ring_size))
        #print(chance_to_propose)
        can_propose_randomly = True
        
        message = None
        while not message:
            if can_propose_randomly and random() < chance_to_propose:
                self.participant = True
                self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time(), 'election', self.channel.id))
                can_propose_randomly = False
                print('Agent %d randomly proposed to be coordinator.' % (self.channel.id))
 
            message = self.channel.receive(30)

        #print('Agent %d received a message.' % (self.channel.id))

        while not (self.participant == False and self.elected != None):

            if message.message_type == 'election':
                
                if message.content > self.channel.id:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time(), 'election', message.content))
                    self.participant = True
                    print('Agent %d forwarded proposal of Agent %d.' % (self.channel.id, message.content))
                elif message.content < self.channel.id and not self.participant:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time(), 'election', self.channel.id))
                    self.participant = True
                    print('Agent %d replaced proposal of Agent %d with its own.' % (self.channel.id, message.content))
                elif message.content == self.channel.id:
                    self.participant = False
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time(), 'elected', self.channel.id))
                    print('Agent %d received its own proposal. Announcing election.' % self.channel.id)

            elif message.message_type == 'elected':
                self.participant = False
                self.elected = message.content
                if message.content != self.channel.id:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time(), 'elected', message.content))
                    print('Agent %d recognizes Agent %d as coordinator.' % (self.channel.id, message.content))
                else:
                    print('Agent %d recognizes itself as coordinator.' % self.channel.id)

            if not (self.participant == False and self.elected != None):
                message = self.channel.receive()

    def start(self):

        self.clock.ntp_sync()
        print('Agent %d synchronized with NTP: %s.' % (self.channel.id, DriftingClock.format_time(self.clock.get_time())))

        self.ring_formation()
        
        self.ring_election()


        
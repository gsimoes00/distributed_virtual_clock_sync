from message import Message
from driftingclock import DriftingClock
from message import Message
from random import random

class Agent(object):
    
    def __init__(self, channel, magnitude=10**(-5), drift=None, ntp_threshold_ms=50):
        
        self.clock = DriftingClock(magnitude, drift)
        self.channel = channel
        self.next_in_ring = None
        self.ring_size = None
        self.participant = False
        self.elected = None
        self.polling_cycle = 0
        self.ntp_reading = 0
        self.ntp_threshold = ntp_threshold_ms
        self.terminate = False

    def receive_wrapper(self, timeout_ms=None):
        message = self.channel.receive(timeout_ms=timeout_ms)
        if message and message.message_type == 'terminate':
            self.terminate = True
            print('Agent %d received order to terminate.' % (self.channel.id))
        return message

    def ring_formation(self):

        received_ping = False
        received_ack = False

        self.channel.send(Message(self.channel.id, [self.channel.id+1], self.clock.get_time_ms(), 'ping', 0))

        while not (received_ping and received_ack):
            message = self.receive_wrapper(self.clock.drifted_ms(100))
            if self.terminate:
                return
            elif message:
                if message.message_type == 'ping' and message.content == 0:
                    received_ping = True
                    self.channel.send(Message(self.channel.id, [message.source], self.clock.get_time_ms(), 'ping', 1))
                elif message.message_type == 'ping' and message.content == 1:
                    received_ack = True
                    self.next_in_ring = message.source
            elif self.channel.id != 1 and not received_ack:
                    self.channel.send(Message(self.channel.id, [1], self.clock.get_time_ms(), 'ping', 0))
        
        print('Agent %d is part of the ring with %d as its successor.' % (self.channel.id, self.next_in_ring))

        if self.next_in_ring == 1:
            print('Agent %d is broadcasting the size of the ring: %d.' % (self.channel.id, self.channel.id))
            self.channel.send(Message(self.channel.id, [], self.clock.get_time_ms(), 'ring_size', self.channel.id))
            self.ring_size = self.channel.id
        else:
            while not self.ring_size:
                message = self.receive_wrapper()
                if self.terminate:
                    return
                if message.message_type == 'ring_size':
                    self.ring_size = message.content

        self.clock.sleep_ms(100)

    def ring_election(self):

        chance_to_propose = 1/((self.ring_size)*(self.ring_size))
        can_propose_randomly = True
        
        message = None
        while not message:
            if can_propose_randomly and random() < chance_to_propose:
                self.participant = True
                self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time_ms(), 'election', self.channel.id))
                can_propose_randomly = False
                print('Agent %d randomly proposed to be coordinator.' % (self.channel.id))
 
            message = self.receive_wrapper(self.clock.drifted_ms(30))
        
        if self.terminate:
            return

        #print('Agent %d received a message.\n%s' % (self.channel.id, str(message.__dict__)))

        while not (self.participant == False and self.elected != None):

            #print('Agent %d entered loop.' % (self.channel.id))

            if message.message_type == 'election':
                
                if message.content > self.channel.id:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time_ms(), 'election', message.content))
                    self.participant = True
                    print('Agent %d forwarded proposal of Agent %d.' % (self.channel.id, message.content))
                elif message.content < self.channel.id and not self.participant:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time_ms(), 'election', self.channel.id))
                    self.participant = True
                    print('Agent %d replaced proposal of Agent %d with its own.' % (self.channel.id, message.content))
                elif message.content == self.channel.id:
                    self.participant = False
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time_ms(), 'elected', self.channel.id))
                    print('Agent %d received its own proposal. Announcing election.' % self.channel.id)

            elif message.message_type == 'elected':
                self.participant = False
                self.elected = message.content
                if message.content != self.channel.id:
                    self.channel.send(Message(self.channel.id, [self.next_in_ring], self.clock.get_time_ms(), 'elected', message.content))
                    print('Agent %d recognizes Agent %d as coordinator.' % (self.channel.id, message.content))
                else:
                    print('Agent %d recognizes itself as coordinator.' % self.channel.id)

            if not (self.participant == False and self.elected != None):
                message = self.receive_wrapper()
                if self.terminate:
                    return
        
        self.clock.sleep_ms(100)

    def coordinator_polling_task(self):
        
        print("Coordinator will start polling for synchronization round %d." % self.polling_cycle)
        time_start = self.clock.get_time_ms()
        self.channel.send(Message(self.channel.id, [], self.clock.get_time_ms(), 'time_polling', self.polling_cycle))

        received_list = []

        default_wait = self.clock.drifted_ms(20)
        wait = default_wait
        while wait > 0:
            message = self.receive_wrapper(wait)
            if message and message.message_type == 'time_polling' and message.content == self.polling_cycle:
                received_list.append([message.source, message.timestamp, self.clock.get_time_ms()])

            wait = default_wait - (self.clock.get_time_ms() - time_start)

        if self.terminate:
            return

        sum = time_start #coordinator
        amount = len(received_list)+1
        for i in range(len(received_list)):
            rtt_2 = (received_list[i][2] - time_start)/2 #RTT/2
            estimated_time = received_list[i][1] - rtt_2 #subordinate
            received_list[i].append(estimated_time)
            sum += estimated_time
        mean = int(sum/amount)
        print('Coordinator received %d responses with mean: %s.' % (amount, DriftingClock.format_time_ms(mean)))

        coordinator_offset = int(mean - time_start)
        #print(coordinator_offset)
        before = self.clock.get_time_ms()
        self.clock.offset += coordinator_offset
        after = self.clock.get_time_ms()
        print('Coordinator adjusted with offset %+d: %s --> %s.' % (coordinator_offset, DriftingClock.format_time_ms(before), DriftingClock.format_time_ms(after)))
        for element in received_list:
            offset = int(mean - element[3])
            #print(offset)
            self.channel.send(Message(self.channel.id, [element[0]], self.clock.get_time_ms(), 'offset', offset))

        self.polling_cycle += 1

    def coordinator_ntp_task(self):
        
        offset = self.clock.ntp_fetch()
        print('Coordinator measured NTP offset as %+d.' % offset)
        if offset > self.ntp_threshold:
            print('NTP offset is too high. Coordinator is sending synchronizing order.')
            before = self.clock.get_time_ms()
            self.clock.offset += offset
            after = self.clock.get_time_ms()
            print('Coordinator synchronized with NTP %+d: %s --> %s.' % (offset, DriftingClock.format_time_ms(before), DriftingClock.format_time_ms(after)))
            self.channel.send(Message(self.channel.id, [], self.clock.get_time_ms(), 'ntp_sync', None))

    def subordinate_loop(self):
        
        while not self.terminate:

            message = self.receive_wrapper()
            if self.terminate:
                return
            
            if message and message.source == self.elected:

                if message.message_type == 'time_polling':
                    self.channel.send(Message(self.channel.id, [self.elected], self.clock.get_time_ms(), 'time_polling', self.polling_cycle))
                    self.polling_cycle += 1
                
                elif message.message_type == 'offset':
                    before = self.clock.get_time_ms()
                    self.clock.offset += message.content
                    after = self.clock.get_time_ms()
                    print('Agent %d adjusted with offset %+d: %s --> %s.' % (self.channel.id, message.content, DriftingClock.format_time_ms(before), DriftingClock.format_time_ms(after)))

                elif message.message_type == 'ntp_sync':
                    before = self.clock.get_time_ms()
                    self.clock.ntp_sync()
                    after = self.clock.get_time_ms()
                    print('Agent %d synchronized with NTP %+d: %s --> %s.' % (self.channel.id, self.ntp_reading, DriftingClock.format_time_ms(before), DriftingClock.format_time_ms(after)))

    def coordinator_loop(self):
        
        ntp_task_counter = 0
        while not self.terminate:
            time_start = self.clock.get_time_ms()

            if ntp_task_counter >= 10:
                self.coordinator_ntp_task()
                ntp_task_counter = 0
            else:
                self.coordinator_polling_task()

            ntp_task_counter += 1
            self.clock.sleep_ms(500 - (self.clock.get_time_ms() - time_start))
    
    def start(self):
        
        before = self.clock.get_time_ms()
        self.ntp_reading = self.clock.ntp_sync()
        after = self.clock.get_time_ms()
        print('Agent %d synchronized with NTP %+d: %s --> %s.' % (self.channel.id, self.ntp_reading, DriftingClock.format_time_ms(before), DriftingClock.format_time_ms(after)))

        if self.terminate:
            return

        self.ring_formation()

        if self.terminate:
            return
        
        self.ring_election()

        if self.terminate:
            return

        if self.elected == self.channel.id:
            self.coordinator_loop()

        else:
            self.subordinate_loop()
        
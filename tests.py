from threading import Thread
from sys import argv

from driftingclock import DriftingClock
from eventscheduler import EventScheduler
from queuecommunication import QueueCommunication
from message import Message

class Test01(object):

    @staticmethod
    def test01_thread(channel):
        clock = DriftingClock(magnitude=10**(-3))
        clock.ntp_sync()

        if channel.id == 1:
            print('Clock %d is the master, sending first message.' % channel.id)
            msg1 = Message(channel.id, [], 'int', clock.get_time())
            channel.send(msg1)

        count = 0
        while count < 100:
            msg_in = channel.receive()
            count += 1
            if msg_in.message_type == None and msg_in.source == 1:
                print('Clock %d was stopped by master.' % channel.id)
                return
            else:
                value = clock.get_time() - msg_in.content
                print('Clock %d - Clock %d + Delay = %+d' % (channel.id, msg_in.source, value))

                msg_out = Message(channel.id, [msg_in.source], 'int', clock.get_time())
                channel.send(msg_out)

        print('Clock %d received 100 messages and stopped.' % channel.id)

        if channel.id == 1:
            print('Master Clock %d is broadcasting stop signal to all clocks.' % channel.id)
            msg_out = Message(channel.id, [], None, None)
            channel.send(msg_out)

    @staticmethod
    def run():

        sch = EventScheduler()
        comm = QueueCommunication(sch)

        num_clocks = 2
        if len(argv) > 1:
            num_clocks = int(argv[1])
            if num_clocks < 2:
                num_clocks = 2

        thread_list = []    
        for _ in range(num_clocks):
            channel = comm.register()
            thread = Thread(target=Test01.test01_thread, args=(channel,))
            thread_list.append(thread)
            thread.start()

        comm.start()

        for thread in thread_list:
            thread.join()

        comm.stop()
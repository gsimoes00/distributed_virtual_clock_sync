
from agent import Agent
from eventscheduler import EventScheduler
from queuecommunication import QueueCommunication
from threading import Thread
from time import sleep
from sys import argv

class SimulationController(object):

    def __init__(self):
        self.scheduler = EventScheduler()
        self.communication = QueueCommunication(self.scheduler)
        self.thread_list = []
        self.num_agents = 2

    def agent_thread(self):
        agent = Agent(self.communication.register())
        agent.start()

    def setup(self):

        if len(argv) > 1:
            try:
                num_agents = int(argv[1])
                if num_agents < 2:
                    num_agents = 2
            except:
                num_agents = 2

        for _ in range(num_agents):
            thread = Thread(target=self.agent_thread, args=())
            self.thread_list.append(thread)

    def start(self):
        for t in self.thread_list:
            t.start()
        self.scheduler.start()
        self.communication.start()

    def stop(self):
        self.communication.issue_terminate_order()
        for t in self.thread_list:
            t.join()
        self.communication.stop()
        self.communication.thread.join()
        self.scheduler.stop()
        self.scheduler.thread.join()

if __name__ == '__main__':

    sim = SimulationController()

    try:

        sim.setup()
        sim.start()

        sleep(60)

        sim.stop()

    except KeyboardInterrupt:
        
        sim.stop()

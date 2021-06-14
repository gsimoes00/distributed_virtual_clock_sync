
from agent import Agent
from eventscheduler import EventScheduler
from queuecommunication import QueueCommunication
from threading import Thread
from time import sleep
from sys import argv

class SimulationController(object):

    USAGE = ['Usage: main.py <num_agents> <drift_magnitude> <ntp_threshold> <time_to_simulate>', 
        'Limits: num_agents > 2; 0.000001 <= drift_magnitude <= 0.1 (s/s); 0 <= ntp_threshold <= 1000 (ms); time_to_simulate > 0.0 (s)']

    def __init__(self):
        self.scheduler = EventScheduler()
        self.communication = QueueCommunication(self.scheduler)
        self.thread_list = []
        self.num_agents = 2
        self.magnitude = 10**(-5)
        self.threshold = 50
        self.sim_time = 60

    def agent_thread(self):
        agent = Agent(channel=self.communication.register(), magnitude=self.magnitude, ntp_threshold_ms=self.threshold)
        agent.start()

    def setup(self):
        valid_input = True
        if len(argv) == 5:
            try:
                self.num_agents = int(argv[1])
                if self.num_agents < 2:
                    valid_input = False

                self.magnitude = float(argv[2])
                if self.magnitude < 10**(-6) or self.magnitude > 10**(-1):
                    valid_input = False

                self.threshold = int(argv[3])
                if self.threshold < 0 or self.threshold > 1000:
                    valid_input = False

                self.sim_time = float(argv[4])
                if self.sim_time < 0:
                    valid_input = False

            except:
                valid_input = False

        elif len(argv) > 1:
            valid_input = False

        if valid_input:
            for _ in range(self.num_agents):
                thread = Thread(target=self.agent_thread, args=())
                self.thread_list.append(thread)
        else:
            print(self.USAGE[0])
            print(self.USAGE[1])
        
        return valid_input

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

        if sim.setup():

            sim.start()

            sleep(60)

            sim.stop()

    
    except KeyboardInterrupt:
        
        sim.stop()

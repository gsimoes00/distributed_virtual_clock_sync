from time import time_ns, perf_counter_ns, strftime, localtime, sleep
from random import betavariate, choice
from ntplib import NTPClient

class DriftingClock(object):

    NTP_HOSTNAME = 'gps.ntp.br'

    def __init__(self, magnitude=10**(-3), drift=None):
        wall_start = time_ns()
        while time_ns() == wall_start:
            pass
        self.perf_counter_start = perf_counter_ns()//1000000
        self.wall_start = time_ns()//1000000
        if drift:
            self.drift = 1 + drift
        else:
            self.drift = 1 + (choice((-1, 1)))*betavariate(10, 2)*magnitude
        self.ntp_client = NTPClient()
        self.ntp_offset = 0

    def get_time_ms(self):
        perf_counter_current = perf_counter_ns()//1000000
        return (self.wall_start + self.ntp_offset + 
            int(self.drift*(perf_counter_current - self.perf_counter_start)))

    def ntp_sync(self):
        response = self.ntp_client.request(DriftingClock.NTP_HOSTNAME, version=3)
        self.ntp_offset = int(response.offset*1000)

    def sleep_ms(self, duration):
        sleep((duration/self.drift)/1000)

    def drifted_time_ms(self, duration):
        return duration/self.drift

    @staticmethod
    def format_time_ms(ms_epoch):
        return strftime("%H:%M:%S.", localtime(ms_epoch//1000)) + str(ms_epoch%1000)

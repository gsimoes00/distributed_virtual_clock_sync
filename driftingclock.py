from time import time_ns, perf_counter_ns, strftime, localtime, sleep
from random import betavariate, choice
from ntplib import NTPClient

class DriftingClock(object):

    NTP_HOSTNAME = 'gps.ntp.br'

    def __init__(self, magnitude=10**(-5), drift=None):
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
        self.offset = 0

    def get_time_ms(self):
        perf_counter_current = perf_counter_ns()//1000000
        return (self.wall_start + self.offset + 
            int(self.drift*(perf_counter_current - self.perf_counter_start)))

    def ntp_sync(self):
        offset = self.ntp_fetch()
        self.offset += offset
        return offset

    def ntp_fetch(self):
        response = self.ntp_client.request(DriftingClock.NTP_HOSTNAME, version=3)
        time_self = self.get_time_ms()
        correct_time = int((response.dest_time + response.offset)*1000)
        offset = (correct_time - time_self)
        return offset

    def sleep_ms(self, duration):
        sleep((duration/self.drift)/1000)

    def drifted_ms(self, duration):
        return int(duration/self.drift)

    def drifted_ms_to_s(self, duration):
        return (duration/self.drift)/1000

    @staticmethod
    def format_time_ms(ms_epoch):
        return strftime("%H:%M:%S.", localtime(ms_epoch//1000)) + str(ms_epoch%1000)

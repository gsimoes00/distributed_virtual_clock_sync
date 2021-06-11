import time
from random import betavariate, choice
from ntplib import NTPClient

class DriftingClock(object):

    NTP_HOSTNAME = 'b.ntp.br'

    def __init__(self, magnitude=10**(-3), drift=None):
        wall_start = time.time_ns()
        while time.time_ns() == wall_start:
            pass
        self.monotonic_start = time.monotonic_ns()//1000000
        self.wall_start = int(time.time()*1000)
        if drift:
            self.drift = 1 + drift
        else:
            self.drift = 1 + (choice((-1, 1)))*betavariate(10, 2)*magnitude
        self.ntp_client = NTPClient()
        self.ntp_offset = 0

    def get_time(self):
        monotonic_current = time.monotonic_ns()//1000000
        return (self.wall_start + self.ntp_offset + 
            int(self.drift*(monotonic_current - self.monotonic_start)))

    def ntp_sync(self):
        response = self.ntp_client.request(DriftingClock.NTP_HOSTNAME, version=3)
        self.ntp_offset = int(response.offset*1000)

    @staticmethod
    def format_time(ms_epoch):
        return time.strftime("%H:%M:%S.", time.localtime(ms_epoch//1000)) + str(ms_epoch%1000)

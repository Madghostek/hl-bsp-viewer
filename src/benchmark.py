import datetime
from enum import Enum


class VerboseLevel(Enum):
    noprint = 0
    nowarnings = 1
    default = 2


class TimerMs:

    logLevel = VerboseLevel.default
    startTimes = {}

    @staticmethod
    def setLogLevel(self, level: VerboseLevel):
        self.logLevel = level

    def __init__(self, banner="[Benchmark]"):
        self.banner = banner

    def start(self, sectionName="Section"):
        if self.logLevel.value > VerboseLevel.nowarnings.value and sectionName in self.startTimes:
            print(self.banner,
                  "warning, section timer reset without end():", sectionName)
        self.startTimes[sectionName] = datetime.datetime.now()

    def end(self, sectionName):
        if self.logLevel.value > VerboseLevel.nowarnings.value and sectionName not in self.startTimes:
            print(self.banner, "warning, section end() without start():", sectionName)
            return 0

        delta = datetime.datetime.now()-self.startTimes[sectionName]
        if self.logLevel.value > VerboseLevel.noprint.value:
            print("->"*len(self.startTimes), sectionName,
                  f"done in {delta/datetime.timedelta(milliseconds=1)}ms")
        del self.startTimes[sectionName]
        return delta

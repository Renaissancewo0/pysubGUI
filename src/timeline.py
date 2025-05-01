from __future__ import annotations
import re
import operator
from functools import total_ordering


class Timeline:
    def __init__(self, start: str, end: str, text: str) -> None:
        self._start = Time(start)
        self._end = Time(end)
        self._text = text
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self!s}>'
    
    def __str__(self) -> str:
        return f'{self.start!s} --> {self.end!s}    {self.text}'
    
    # These two defined to support being a key of dict
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Timeline):
            return NotImplemented
        return (self.start == other.start
                and self.end == other.end
                and self.text == other.text)

    def __hash__(self) -> int:
        return hash((self.start, self.end, self.text))
    
    # Defined to support sort
    def __lt__(self, other: Timeline) -> bool:
        return self.start < other.start

    @property
    def start(self):
        return self._start

    @property
    def end(self):
        return self._end
    
    @property
    def text(self):
        return self._text
    
    def merge(self, other: Timeline) -> Timeline:
        return Timeline(self.start, other.end, self.text)
    
    def key(self):
        return (self.start, self.end)

@total_ordering
class Time:
    def __init__(self, timeStamp: str) -> None:
        if isinstance(timeStamp, Time):
            self._time = timeStamp.time
        else:
            self._time = Time.parse(timeStamp)
    
    def __repr__(self) -> str:
        return f'<{self.__class__.__name__}: {self!s}>'
    
    def __str__(self) -> str:
        t = self.time
        # millisecond, second, minute, hour
        units = [1000, 60, 60, 24]
        time = []
        # Reconstruct from millisecond
        for u in units:
            time.append(t % u)
            t //= u
        return f'{time[3]:02d}:{time[2]:02d}:{time[1]:02d}.{time[0]:03d}'
    
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Time):
            return NotImplemented
        return self.time == other.time
    
    def __lt__(self, other: Time) -> bool:
        return self.time < other.time
    
    def __hash__(self) -> int:
        return hash(self.time)
    
    @property
    def time(self):
        return self._time
    
    @staticmethod
    def parse(timeStamp: str) -> int:
        '''Save the timestamp as an integer in unit of millisecond'''
        time = re.split(r':|,|[.]', timeStamp)
        # For ASS file, milliseconds has only two digits, add 0
        if len(time[-1]) == 2:
            time[-1] += '0'
        # Convert to millisecond
        units = [3_600_000, 60_000, 1_000, 1]
        return sum(map(operator.mul, map(int, time), units))


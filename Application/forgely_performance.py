"""Bounded, thread-safe timings in milliseconds; no screen data stored."""
from collections import defaultdict, deque
from threading import Lock

class PerformanceTracker:
    def __init__(self, capacity=256):
        self.capacity = capacity
        self.samples = defaultdict(lambda: deque(maxlen=self.capacity))
        self.lock = Lock()

    def record(self, stage: str, duration_ns: int) -> None:
        with self.lock:
            self.samples[stage].append(max(0, duration_ns) / 1_000_000)

    def snapshot(self) -> dict:
        with self.lock:
            data = {k: sorted(v) for k,v in self.samples.items()}
        def percentile(values, fraction):
            return values[max(0, min(len(values)-1, int((len(values)-1)*fraction + .5)))]
        return {key: {'count':len(values), 'p50':percentile(values,.50),
                      'p95':percentile(values,.95), 'p99':percentile(values,.99),
                      'max':values[-1]} for key,values in data.items() if values}

"""Walk-forward split generator for leakage-resistant strategy evaluation."""
from dataclasses import dataclass

@dataclass(frozen=True)
class WalkForwardWindow:
    train_start: int
    train_end: int
    test_start: int
    test_end: int

class WalkForwardSplitter:
    def __init__(self, train_size: int, test_size: int, step=None):
        if train_size <= 0 or test_size <= 0: raise ValueError("window sizes must be positive")
        self.train_size=train_size; self.test_size=test_size; self.step=step or test_size
        if self.step <= 0: raise ValueError("step must be positive")
    def split(self, n_samples: int):
        if n_samples < self.train_size + self.test_size: return []
        windows=[]; start=0
        while start+self.train_size+self.test_size <= n_samples:
            train_end=start+self.train_size
            windows.append(WalkForwardWindow(start,train_end,train_end,train_end+self.test_size))
            start += self.step
        return windows

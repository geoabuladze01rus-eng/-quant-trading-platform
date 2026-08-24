"""Walk-forward validation to reduce backtest overfitting."""
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Window: train_start:int; train_end:int; test_start:int; test_end:int
@dataclass(frozen=True)
class WindowResult: window:Window; train_score:float; test_score:float; passed:bool
class WalkForwardValidator:
    def __init__(self,train_size:int,test_size:int,step:int|None=None,min_test_score:float=0.0): self.train_size=train_size; self.test_size=test_size; self.step=step or test_size; self.min_test_score=min_test_score
    def windows(self,n:int)->list[Window]:
        out=[]; start=0
        while start+self.train_size+self.test_size<=n: out.append(Window(start,start+self.train_size,start+self.train_size,start+self.train_size+self.test_size)); start+=self.step
        return out
    def validate(self,data:Sequence[Any],fit_score:Callable[[Sequence[Any]],float],test_score:Callable[[Sequence[Any]],float])->list[WindowResult]:
        out=[]
        for w in self.windows(len(data)):
            tr=data[w.train_start:w.train_end]; te=data[w.test_start:w.test_end]; ts=float(test_score(te)); out.append(WindowResult(w,float(fit_score(tr)),ts,ts>=self.min_test_score))
        return out

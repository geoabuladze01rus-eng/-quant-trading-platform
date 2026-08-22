"""Leakage-resistant walk-forward evaluation with train/validation/OOS windows."""
from dataclasses import dataclass
from typing import Any, Callable, Sequence
@dataclass(frozen=True)
class WalkForwardWindow:
    train:tuple[Any,...]; validation:tuple[Any,...]; test:tuple[Any,...]
@dataclass(frozen=True)
class WalkForwardResult:
    index:int; train_result:Any; validation_result:Any; test_result:Any
class WalkForwardSplitter:
    def __init__(self,train_size:int,validation_size:int,test_size:int,step:int|None=None):
        if min(train_size,validation_size,test_size)<=0: raise ValueError("window sizes must be positive")
        self.train_size=train_size; self.validation_size=validation_size; self.test_size=test_size; self.step=step or test_size
        if self.step<=0: raise ValueError("step must be positive")
    def split(self,events:Sequence[Any])->list[WalkForwardWindow]:
        windows=[]; start=0; width=self.train_size+self.validation_size+self.test_size
        while start+width<=len(events):
            a=start+self.train_size; b=a+self.validation_size; c=b+self.test_size
            windows.append(WalkForwardWindow(tuple(events[start:a]),tuple(events[a:b]),tuple(events[b:c]))); start+=self.step
        return windows
    def evaluate(self,events:Sequence[Any],fit:Callable[[tuple[Any,...]],Any],score:Callable[[Any,tuple[Any,...]],Any])->tuple[WalkForwardResult,...]:
        out=[]
        for i,w in enumerate(self.split(events)):
            model=fit(w.train); out.append(WalkForwardResult(i,score(model,w.train),score(model,w.validation),score(model,w.test)))
        return tuple(out)

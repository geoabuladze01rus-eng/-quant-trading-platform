"""Bounded parameter search with deterministic selection and overfit-aware scoring."""
from dataclasses import dataclass
from itertools import product
from typing import Any, Callable, Mapping, Sequence
@dataclass(frozen=True)
class CandidateResult: params:Mapping[str,Any]; train_score:float; validation_score:float; robust_score:float
class ParameterSearch:
    def __init__(self,min_validation_score:float=0.0): self.min_validation_score=min_validation_score
    def run(self,grid:Mapping[str,Sequence[Any]],score:Callable[[Mapping[str,Any],str],float])->CandidateResult|None:
        best=None; keys=list(grid)
        for values in product(*(grid[k] for k in keys)):
            params=dict(zip(keys,values)); tr=float(score(params,"train")); va=float(score(params,"validation")); robust=min(tr,va)
            if va<self.min_validation_score: continue
            candidate=CandidateResult(params,tr,va,robust)
            if best is None or (candidate.robust_score,candidate.validation_score)>(best.robust_score,best.validation_score): best=candidate
        return best

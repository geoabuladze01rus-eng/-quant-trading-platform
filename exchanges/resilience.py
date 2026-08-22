"""Shared retry, backoff and rate-limit policy for exchange adapters."""
from dataclasses import dataclass
from random import uniform
from typing import Callable,TypeVar
T=TypeVar("T")
@dataclass(frozen=True)
class RetryPolicy:
    max_attempts:int=3; base_delay_ms:int=100; max_delay_ms:int=2000; jitter:float=0.2
class RetryableExchangeError(Exception): pass
class RateLimitExceeded(RetryableExchangeError): pass
class ExchangeResilience:
    def __init__(self,policy:RetryPolicy|None=None): self.policy=policy or RetryPolicy()
    def call(self,fn:Callable[[],T])->T:
        last=None
        for attempt in range(self.policy.max_attempts):
            try:return fn()
            except RetryableExchangeError as exc:
                last=exc
                if attempt+1>=self.policy.max_attempts:break
        raise last
    def delay_ms(self,attempt:int)->int:
        raw=min(self.policy.max_delay_ms,self.policy.base_delay_ms*(2**attempt)); return int(raw*(1+uniform(-self.policy.jitter,self.policy.jitter)))

"""Walk-forward validation: sequential train/validation/test windows."""
from dataclasses import dataclass
from typing import Sequence, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class WalkForwardWindow:
    train: Sequence[T]
    validation: Sequence[T]
    test: Sequence[T]


def windows(data: Sequence[T], train_size: int, validation_size: int, test_size: int, step: int | None = None) -> list[WalkForwardWindow]:
    if min(train_size, validation_size, test_size) <= 0:
        raise ValueError("window sizes must be positive")
    step = step or test_size
    if step <= 0:
        raise ValueError("step must be positive")
    result: list[WalkForwardWindow] = []
    start = 0
    while start + train_size + validation_size + test_size <= len(data):
        a = start + train_size
        b = a + validation_size
        c = b + test_size
        result.append(WalkForwardWindow(data[start:a], data[a:b], data[b:c]))
        start += step
    return result


def select_best(scores: Sequence[tuple[float, object]]) -> object:
    if not scores:
        raise ValueError("no validation scores")
    return max(scores, key=lambda item: item[0])[1]

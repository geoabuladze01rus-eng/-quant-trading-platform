import pytest

from backtesting.walk_forward import select_best, windows


def test_windows_are_sequential_and_non_overlapping() -> None:
    data = list(range(20))
    result = windows(data, train_size=10, validation_size=4, test_size=4)
    assert len(result) == 1
    assert list(result[0].train) == list(range(10))
    assert list(result[0].validation) == list(range(10, 14))
    assert list(result[0].test) == list(range(14, 18))


def test_walk_forward_rejects_invalid_sizes() -> None:
    with pytest.raises(ValueError):
        windows([1, 2, 3], 0, 1, 1)


def test_select_best_uses_validation_score() -> None:
    assert select_best([(0.2, "a"), (0.7, "b"), (0.3, "c")]) == "b"

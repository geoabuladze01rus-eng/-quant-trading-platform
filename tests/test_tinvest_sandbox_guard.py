import pytest

from connectors.tinvest.transport import SandboxOnlyGuard


def test_sandbox_guard_accepts_sandbox_url() -> None:
    SandboxOnlyGuard("https://sandbox.example.invalid")


def test_sandbox_guard_rejects_production_url() -> None:
    with pytest.raises(ValueError):
        SandboxOnlyGuard("https://api.example.invalid")

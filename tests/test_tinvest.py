from decimal import Decimal

import pytest

from quant_platform.connectors.tinvest import TInvestConnector
from quant_platform.domain import Side


@pytest.mark.asyncio
async def test_sandbox_account_and_order_payloads(monkeypatch) -> None:
    connector = TInvestConnector("test-token", sandbox=True)
    calls: list[tuple[str, dict]] = []

    async def fake_post(method: str, payload: dict) -> dict:
        calls.append((method, payload))
        if method.endswith("OpenSandboxAccount"):
            return {"accountId": "sandbox-1"}
        return {"orderId": "order-1"}

    monkeypatch.setattr(connector, "_post", fake_post)
    account_id = await connector.open_sandbox_account()
    assert account_id == "sandbox-1"
    await connector.sandbox_pay_in(account_id, Decimal("1000.25"))
    await connector.submit_sandbox_order(account_id, "uid-1", 2, Side.BUY)

    assert calls[1][1]["amount"]["units"] == "1000"
    assert calls[1][1]["amount"]["nano"] == 250000000
    assert calls[2][1]["direction"] == "ORDER_DIRECTION_BUY"


def test_live_execution_is_disabled() -> None:
    connector = TInvestConnector("test-token", sandbox=False)
    with pytest.raises(RuntimeError, match="disabled"):
        import asyncio
        asyncio.run(connector.submit_live(None))

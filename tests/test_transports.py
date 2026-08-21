import asyncio
from marketdata.transports import ReconnectingTransport, TransportConfig

class FakeClient:
    def __init__(self, messages):
        self.messages = iter(messages)
        self.closed = False
    async def connect(self):
        return None
    async def receive(self):
        try:
            return next(self.messages)
        except StopIteration:
            raise RuntimeError("feed closed")
    async def close(self):
        self.closed = True

def test_transport_forwards_messages_and_stops_after_retry_limit():
    received = []
    clients = [FakeClient(["a"]), FakeClient(["b"])]
    def factory():
        async def make():
            return clients.pop(0)
        return make()
    async def on_message(message):
        received.append(message)
    async def run():
        transport = ReconnectingTransport(factory, on_message, TransportConfig(0, 0, 2))
        try:
            await transport.run()
        except RuntimeError:
            pass
        return transport
    transport = asyncio.run(run())
    assert received == ["a", "b"]
    assert transport.running is False

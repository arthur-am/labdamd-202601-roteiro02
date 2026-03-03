import asyncio
from enum import Enum

class ConnectionState(Enum):
    CONNECTED    = "connected"
    MIGRATING    = "migrating"
    RECONNECTING = "reconnecting"

class TransparentWSClient:
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.state = ConnectionState.CONNECTED
        self._ws = None
        self._message_buffer = []

    async def send(self, msg: str):
        if self.state == ConnectionState.MIGRATING:
            self._message_buffer.append(msg)
            return
        if self._ws:
            await self._ws.send(msg)

    async def _handle_relocation(self, new_endpoint: str):
        self.state = ConnectionState.MIGRATING
        print(f"Relocando conexao para {new_endpoint}...")
        self.state = ConnectionState.RECONNECTING
        for buffered_msg in self._message_buffer:
            await self._ws.send(buffered_msg)
        self._message_buffer.clear()
        self.state = ConnectionState.CONNECTED
        print("Relocacao concluida — buffer drenado.")
import asyncio

from .shutter_protocol import ShutterProtocol


class ShutterTCP(ShutterProtocol):
    eol_write = b"\r\n"
    eol_read = b"\r"

    def __init__(self, reader, writer):
        self._reader = reader
        self._writer = writer

    @classmethod
    async def connect(cls, host, port=80, **kwargs):
        reader, writer = await asyncio.open_connection(host, port, **kwargs)
        return cls(reader, writer)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def close(self):
        self._writer.close()

    def _writeline(self, cmd):
        self._writer.write(cmd + self.eol_write)

    async def _readline(self):
        r = b""
        while not r.endswith(self.eol_read):
            r += await self._reader.read(1)
        return r[:-len(self.eol_read)]

    async def _read(self, n):
        return await self._reader.read(n)

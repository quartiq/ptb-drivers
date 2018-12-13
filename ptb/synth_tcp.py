import asyncio

from .synth_protocol import SynthProtocol


class SynthTCP(SynthProtocol):
    eol_write = b"\n"
    eol_read = b"\n"

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
        self._writer.write(cmd.encode() + self.eol_write)

    async def _readline(self):
        r = await self._reader.readline()
        assert r.endswith(self.eol_read)
        return r[:-len(self.eol_read)].decode()

    async def _read(self, n):
        return await self._reader.read(n)

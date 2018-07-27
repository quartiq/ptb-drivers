import logging
import asyncio

logger = logging.getLogger(__name__)


class ShutterProtocol:
    """Protocol for the PTB multi-channel shutter controller"""

    def do(self, cmd):
        assert len(cmd) <= 2
        logger.debug("do %s", cmd)
        self._writeline(cmd)

    async def ask(self, cmd):
        self.do(cmd)
        ret = await self._readline()
        logger.debug("ret %s", ret)
        return ret

    async def read(self, n):
        ret = await self._read(n)
        return ret.decode()

    async def version(self):
        """Return the hardware/firmware version.

        Returns:
            str: Version string.
        """
        return (await self.ask(b"v")).strip()

    async def status(self):
        """Return the error flags on all channels.

        Returns:
            list(float): Temperatures on all channels
        """
        ret = (await self.ask(b"e")).strip()
        assert len(ret) == 3
        return tuple(bool(int(_)) for _ in ret)

    def clear(self):
        """Clear all error flags."""
        self.do(b"r")

    async def passthrough(self, shutter, cmd):
        """Execute a low level command.

        Args:
            shutter (int): Shutter index (1-3)
            cmd (bytes(1)): Single character command (e.g. W)

        Return:
            bytes: Response
        """
        return await self.ask("{:d}".encode() + cmd)

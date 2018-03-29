import logging
import asyncio

logger = logging.getLogger(__name__)


class TempProtocol:
    """Protocol for the PTB multi-channel temperature sensor"""

    def do(self, cmd):
        assert len(cmd) < 64
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
        return (await self.ask("v")).strip()

    async def get_all(self):
        """Measure and return the temperatures on all channels.

        Returns:
            list(float): Temperatures on all channels
        """
        ret = await self.ask("a")
        t = []
        for i, ti in enumerate(ret.split()):
            ch, ti = ti.split(":")
            assert int(ch) == i
            t.append(float(ti))
        return t

    async def get(self, channel):
        """Measure the temperature on one channel.

        Args:
            channel (int): Channel index to measure on

        Return:
            float: Temperature
        """
        ret = await self.ask("{:d}".format(channel))
        ch, temp = ret.split(":")
        assert int(ch) == channel
        return float(temp)

    def _writeline(self, cmd):
        raise NotImplemented

    async def _readline(self):
        raise NotImplemented

    async def ping(self):
        try:
            await self.version()
        except asyncio.CancelledError:
            raise
        except:
            logger.warning("ping failed", exc_info=True)
            return False
        return True

import logging
import asyncio

from .adf4350 import ADF4350

logger = logging.getLogger(__name__)


class SynthProtocol(ADF4350):
    """Protocol for the PTB synthesizer (ADF4350-based)"""
    poll_interval = .01

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

    def set(self, **kwargs):
        """Configure synthesizer settings.

        See datasheet and :class:`ADF4350` for fields and values.

        This does not update the synthesizer settings or registers.
        This method only sets instance attributes that affect the
        calculation of register values during :meth:`set_frequency`.
        """
        for k, v in kwargs.items():
            if not hasattr(self, k):
                raise ValueError("No such field `{}`".format(k))
            setattr(self, k, v)

    def get(self, key):
        """Get a synthesizer configuration setting (instance attribute)."""
        return getattr(self, key)

    async def version(self):
        """Return the hardware/firmware version.

        Returns:
            str: Version string.
        """
        self.do("version")
        return (await self.read(7)).strip()

    def _fmt_regs(self, regs):
        return "{:08x}{:08x}{:08x}{:08x}{:08x}{:08x}".format(*regs)

    async def start(self, regs=None):
        """Send the six registers to the synthesizer.

        Args:
            regs (list(int), optional): 32 bit register values
                (reg5 down to reg0). If no register values are passed, then
                the ones calculated by :meth:`set_frequency` are used.
        """
        if regs is None:
            regs = reversed(self._regs)
        cmd = "start{}".format(self._fmt_regs(regs))
        assert len(cmd) == 5 + 6*8
        self.do(cmd)
        ret = (await self.read(4)).strip()
        if ret != "ok":
            raise ValueError("start failed", ret)

    async def save(self, regs=None):
        """Save the six registers to the EEPROM.
        That data is loaded on boot of the synthesizer.

        Args:
            regs (list(int), optional): 32 bit register values
                (reg5 down to reg0). If no register values are passed, then
                the ones calculated by :meth:`set_frequency` are used.
        """
        if regs is None:
            regs = reversed(self._regs)
        cmd = "save {}".format(self._fmt_regs(regs))
        assert len(cmd) == 5 + 6*8
        self.do(cmd)
        ret = await self.read(4).strip()
        if ret != "ok":
            raise ValueError("save failed", ret)

    async def locked(self):
        """Return the reference lock status.

        Returns:
            bool: True if locked
        """
        return not "not" in await self.ask("locked")

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

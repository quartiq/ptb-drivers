import logging
import asyncio

logger = logging.getLogger(__name__)


class VoltageProtocol:
    """Protocol for the PTB multi-channel voltage source"""

    def do(self, cmd):
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
        return (await self.ask("get version")).strip()

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

    async def _cmd(self, action, name, args=""):
        assert action in ("get", "set")
        cmd = "{} {}".format(action, name)
        ret = await self.ask(cmd + args)
        assert ret.startswith(cmd)
        return ret[len(cmd):].strip()

    async def get_temperature(self):
        """Get temperature data for controller and amplifier
        boards.

        Returns:
            list(float): Raw ADC values for the NTCs
        """
        ret = await self._cmd("get", "temp")
        return [int(_) for _ in ret.split()]

    def ldac(self):
        """Pulse LDAC to all DACs to load values into active registers."""
        return self._cmd("set", "ldac")

    def factory(self):
        """Reset gains and offsets to default values"""
        return self._cmd("set", "factory")

    async def _values(self, action, name, values, channels=None):
        if channels is None:
            channels = list(range(1, len(values) + 1))
        args = " ".join("{} {}".format(channel, value)
                        for channel, value in zip(channels, values))
        ret = await self._cmd(action, name,
                              " {} {}".format(len(values), args))
        v = ret.split()
        assert len(v) % 2 == 1
        n = int(v.pop(0))
        assert len(v) == 2*n
        channels_ret = [int(_) for _ in v[::2]]
        values_ret = v[1::2]
        assert channels_ret == channels
        # assert values_ret == values
        return values_ret, channels_ret

    async def set_voltage(self, values, channels=None):
        """Set output voltages. Voltages become active only after
        :meth:`ldac`.

        Args:
            values (list(float)): Voltages, one for each target channel.
            channels (list(int)): Target channels. Defaults to 1...len(values)

        Returns:
            list(float): Actual values returned by the device.
        """
        values = ["{:.4f}".format(_) for _ in values]
        values, channels = await self._values("set", "volt", values, channels)
        values = [float(_) for _ in values]
        return values, channels

    async def set_gain(self, values, channels=None):
        """Set channel gains. Channel gains are processed within the
        microcontroller and become active on :meth:`set_volt` and a subsequent
        :meth:`ldac`.

        Gains are given in `2**16/full_scale` where
        `full_scale = u_max - u_min`.

        Args:
            values (list(float)): Gains, one for each target channel.
            channels (list(int)): Target channels. Defaults to 1...len(values)

        Returns:
            list(float): Actual values returned by the device.
        """
        values = ["{:.4f}".format(_) for _ in values]
        values, channels = await self._values("set", "gain", values, channels)
        values = [float(_) for _ in values]
        return values, channels

    async def set_offset(self, values, channels=None):
        """Set channel offsets. Channel gains are processed within the
        microcontroller and become active on :meth:`set_volt` and a subsequent
        :meth:`ldac`.

        Offsets are given in DAC LSBs (integers).

        Args:
            values (list(int)): Offsets, one for each target channel.
            channels (list(int)): Target channels. Defaults to 1...len(values)

        Returns:
            list(int): Actual values returned by the device.
        """
        values = ["{:d}".format(_) for _ in values]
        values, channels = await self._values("set", "offset", values, channels)
        values = [int(_) for _ in values]
        return values, channels

    async def set_data(self, values, channels=None):
        """Set raw channel output values. Values are given in DAC LSBs
        (integers). Data becomes active only after :meth:`ldac`.

        Args:
            values (list(int)): DAC values, one for each target channel.
            channels (list(int)): Target channels. Defaults to 1...len(values)

        Returns:
            list(int): Actual values returned by the device.
        """
        values = ["{:d}".format(_) for _ in values]
        values, channels = await self._values("set", "data", values, channels)
        values = [int(_) for _ in values]
        return values, channels

    async def get_data(self, channels=None):
        """Get raw channel output values. Values are given in DAC LSBs
        (integers).

        Args:
            channels (list(int)): Target channels. Defaults to 1...8

        Returns:
            list(int)): DAC values, one for each target channel.
        """
        if channels is None:
            channels = list(range(1, 8 + 1))
        values = ["0" for i in range(len(channels))]
        values, channels = await self._values("get", "data", values, channels)
        values = [int(_) for _ in values]
        return values, channels

import time
import logging
import asyncio
import timeit

from ptb.tcp import SynthTCP as Synth

"""
FIXMES:

hardware:
    * signal AFE to uC by pins (x2, x3 etc)
firmware:
    * readback of registers
    * framing of commands (don't wait for eop but eol)
    * consistent replies
"""


async def test(dev):
    print(dev)
    print(await dev.version())
    await dev.start([  # 2 GHz -14 dBm, from app, reversed
        0x00640000,
        0x08008009,
        0x02004E42,
        0x000404B3,
        0x009C803C,
        0x00580005])
    dev.set_frequency(2e9)
    await dev.start()

def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await Synth.connect("172.21.24.51") as dev:
            await test(dev)
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

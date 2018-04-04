import time
import logging
import asyncio
import timeit

from ptb.voltage_tcp import VoltageTCP as Voltage


async def test(dev):
    print(dev)
    print(await dev.version())
    print(await dev.ping())


def main():
    logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await Voltage.connect("10.32.4.171") as dev:  # ascari
            await test(dev)
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

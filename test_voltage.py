import time
import logging
import asyncio
import timeit

from ptb.voltage_tcp import VoltageTCP as Voltage


async def test(dev):
    print(dev)
    print(await dev.version())
    print(await dev.ping())
    print(await dev.get_temperature())
    t0 = time.time()
    for i in range(2):
        print(await dev.set_voltage([100, -123.45, 5.0], [1, 4, 7]))
        print(await dev.set_ldac())
    print((time.time() - t0)/2)
    print(await dev.get_data())

def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await Voltage.connect("ascari") as dev:
            await test(dev)
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

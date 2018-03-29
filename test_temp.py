import time
import logging
import asyncio
import timeit

from ptb.temp_tcp import TempTCP as Temp


async def test(dev):
    print(dev)
    print(await dev.version())
    print(await dev.ping())
    print(await dev.get_all())
    for i in range(6):
        print(i, await dev.get(i))


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await Temp.connect("10.32.4.156") as dev:  # piquet
            await test(dev)
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

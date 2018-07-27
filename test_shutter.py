import time
import logging
import asyncio
import timeit

from ptb.shutter_tcp import ShutterTCP as Shutter


async def test(dev):
    print(dev)
    print(await dev.version())
    print(await dev.status())
    print(await dev.passthrough(1, b"W"))

def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        with await Synth.connect("buemi") as dev:
            await test(dev)
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

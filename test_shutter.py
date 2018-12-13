import time
import logging
import asyncio
import timeit

from ptb.shutter_tcp import ShutterTCP as Shutter


async def test(dev):
    print(dev)
    print(await dev.status())
    print(await dev.clear())
    print(await dev.version())
    for i in b"":  # STWXYZ
        print(chr(i), await dev.passthrough(1, i))

def main():
    #logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        for d in "palmer button".split():
            print(d)
            with await Shutter.connect(d) as dev:
                await test(dev)

    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

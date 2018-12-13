import time
import logging
import asyncio
import timeit

from ptb.synth_tcp import SynthTCP as Synth

"""
FIXMEs:

hardware:
    * signal AFE to uC by pins (x2, x3, output amp etc)
firmware:
    * readback locked status (muxout)
    * framing of commands (don't wait for eop but eol)
    * consistent replies (framing)
    * mac address
    * dhcp
    * return ID (serial, mac address), together with AFE type
"""


async def test(dev):
    #await dev.start([  # 2 GHz -14 dBm, from app, reversed
    #    0x00640000,
    #    0x08008009,
    #    0x02004E42,
    #    0x000404B3,
    #    0x009C803C,
    #    0x00580005])
    #dev.set_frequency(2e9)
    #await dev.start()
    print(await dev.locked())

def main():
    # logging.basicConfig(level=logging.DEBUG)
    loop = asyncio.get_event_loop()
    loop.set_debug(False)
    async def run():
        for i, host in enumerate("badoer clark hill prost".split()):
            with await Synth.connect(host) as dev:
                # await test(dev)
                print(dev)
                print(await dev.version())
                dev.ref_frequency = 100e6
                dev.ref_div_factor = 4
                dev.ref_div2_en = False
                dev.ref_doubler_en = False
                dev.mute_till_lock_en = True
                dev.output_power = 0
                dev.set_frequency([3.07e9, 5.257e9/2, 14.748e9/6, 2.105e9][i])
                await dev.start()
                print(await dev.locked())
    loop.run_until_complete(run())


if __name__ == "__main__":
    main()

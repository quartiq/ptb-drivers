#!/usr/bin/env python3

import argparse
import logging
import sys
import asyncio

from .synth_tcp import SynthTCP as Synth

from sipyco.pc_rpc import Server
from sipyco import common_args

from sipyco.common_args import (
    simple_network_args, init_logger_from_args as init_logger,
    bind_address_from_args, verbosity_args)


logger = logging.getLogger(__name__)


def get_argparser():
    parser = argparse.ArgumentParser(
        description="""PTB synthesizer controller.""")
    parser.add_argument(
        "-d", "--device", default=None,
        help="Device host name or IP address.")
    simple_network_args(parser, 3262)
    verbosity_args(parser)
    return parser


def main():
    args = get_argparser().parse_args()
    init_logger(args)

    if args.device is None:
        print("You need to supply a -d/--device "
              "argument. Use --help for more information.")
        sys.exit(1)

    loop = asyncio.get_event_loop()

    async def run():
        with await Synth.connect(args.device, loop=loop) as dev:
            server = Server({"ptb_synth": dev}, None, True)
            await server.start(bind_address_from_args(args), args.port)
            try:
                await server.wait_terminate()
            finally:
                await server.stop()

    try:
        loop.run_until_complete(run())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()


if __name__ == "__main__":
    main()

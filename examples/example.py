#!/usr/bin/env python

from bitmex_websocket import Instrument
from bitmex_websocket.constants import InstrumentChannels

import alog
import logging
import signal
import websocket


class Ticker(Instrument):
    def __init__(self, symbol='XBTUSD', **kwargs):
        websocket.enableTrace(True)

        channels = [
            InstrumentChannels.quote,
        ]

        super().__init__(symbol=symbol, channels=channels, **kwargs)

    def on_action(self, message):
        alog.info(alog.pformat(message['data']))


def main():
    emitter = Ticker('XBTUSD')
    emitter.run_forever()


if __name__ == '__main__':
    alog.set_level(logging.DEBUG)
    signal.signal(signal.SIGINT, lambda: exit(0))
    signal.signal(signal.SIGTERM, lambda: exit(0))
    main()

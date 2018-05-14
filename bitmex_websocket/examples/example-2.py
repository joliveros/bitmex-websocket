import asyncio
import logging

import alog
import websocket

from bitmex_websocket import Instrument

websocket.enableTrace(True)


def on_action(data):
    alog.debug(data)


channels = [
    'quote',
    'trade',
    'orderBookL2'
]

XBTUSD = Instrument(symbol='XBTUSD',
                    channels=channels,
                    max_table_length=1,
                    should_auth=False)

XBTUSD.on('action', on_action)

XBTUSD.connect()

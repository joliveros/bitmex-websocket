from __future__ import absolute_import
from bitmex_websocket import Instrument
import asyncio
import websocket

websocket.enableTrace(True)

XBTUSD = Instrument(symbol='XBTUSD',
                    channels=['quote'],
                    maxTableLength=1,
                    shouldAuth=False)


def on_table(table_name, table):
    print(table_name)
    print(table)


XBTUSD.on('quote', on_table)

loop = asyncio.get_event_loop()
loop.run_forever()

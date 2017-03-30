from __future__ import absolute_import
from bitmex_websocket import Instrument
import asyncio
import websocket

websocket.enableTrace(True)


def on_table(table_name, table):
    print("recieved table: %s" % (table_name))
    print(table)


channels = ['quote', 'trade']
XBTUSD = Instrument(symbol='XBTUSD',
                    channels=channels,
                    maxTableLength=1,
                    shouldAuth=False)


for channel in channels:
    XBTUSD.on(channel, on_table)


loop = asyncio.get_event_loop()
loop.run_forever()

from __future__ import absolute_import
from bitmex_websocket import Instrument
import asyncio
import websocket

websocket.enableTrace(True)

XBTH17 = Instrument(symbol='XBTH17',
                    channels=['instrument'],
                    maxTableLength=1,
                    shouldAuth=False)

XBTH17.on('action', lambda x: print("# action message: %s" % x))

loop = asyncio.get_event_loop()
loop.run_forever()

from __future__ import absolute_import
from bitmex_websocket.instrument import Instrument
from time import sleep
import logging
import websocket

_logger = logging.getLogger('websocket')
_logger.setLevel(logging.DEBUG)
websocket.enableTrace(True)

XBTH17 = Instrument(symbol='XBTH17', channels=['instrument'])

while True:
    sleep(1)

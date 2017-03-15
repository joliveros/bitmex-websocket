from __future__ import absolute_import
from bitmex_websocket.websocket import BitMEXWebsocket
from time import sleep
import logging
import websocket

_logger = logging.getLogger('websocket')
_logger.setLevel(logging.DEBUG)
websocket.enableTrace(True)

ws = BitMEXWebsocket()
ws.connect()
ws.subscribe('instrument_')

while True:
    sleep(1)

from __future__ import absolute_import
from bitmex_websocket.websocket import BitMEXWebsocket
from time import sleep

ws = BitMEXWebsocket()
ws.connect()

while True:
    sleep(1)

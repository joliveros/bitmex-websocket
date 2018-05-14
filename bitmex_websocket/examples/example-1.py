import alog

from bitmex_websocket import BitMEXWebsocket
import websocket

websocket.enableTrace(True)

ws = BitMEXWebsocket(ping_interval=5, ping_timeout=4)
# ws.subscribe_action('instrument_')

ws.connect()

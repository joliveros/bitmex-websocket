from bitmex_websocket import BitMEXWebsocket
import websocket

websocket.enableTrace(True)

ws = BitMEXWebsocket(ping_interval=5, ping_timeout=4)

ws.run_forever()

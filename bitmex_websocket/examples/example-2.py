import websocket

from bitmex_websocket import Instrument
from bitmex_websocket.constants import InstrumentChannels

websocket.enableTrace(True)


channels = [
    InstrumentChannels.quote,
    InstrumentChannels.trade,
    InstrumentChannels.orderBookL2
]

XBTUSD = Instrument(symbol='XBTUSD',
                    channels=channels)

XBTUSD.run_forever()

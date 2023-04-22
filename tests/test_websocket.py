import json

from bitmex_websocket import BitMEXWebsocket
from tests.helpers import message_fixtures

orderBookL2_data = message_fixtures()['orderBookL2']


class TestWebsocket(object):
    def test_connect_should_connect_ws(self, mocker):
        socket = BitMEXWebsocket()

        assert socket.gen_url() == \
            'wss://www.bitmex.com/realtime?heartbeat=true'

    def test_subscribe_to_channel(self, mocker):
        socket = BitMEXWebsocket()
        message = {
            "success": "true",
            "subscribe": "instrument:XBTH17",
            "request": {
                "op": "subscribe",
                "args": ["instrument:XBTH17"]
            }
        }

        handler = mocker.stub()
        socket.on('subscribe', handler)
        socket.on_message(socket, json.dumps(message))
        handler.assert_called_once()

    def test_subscribe_instrument_on_message(self, mocker):
        socket = BitMEXWebsocket()
        message = {
            "success": "true",
            "subscribe": "instrument:XBTH17",
            "request": {
                "op": "subscribe",
                "args": ["instrument:XBTH17"]
            }
        }
        subscribe_handler = mocker.stub()

        @socket.on('subscribe')
        def handler(message):
            subscribe_handler(message)

        socket.on_message(socket, json.dumps(message))

        subscribe_handler.assert_called_once_with(message)

    def test_on_subscribe_success(self, mocker):
        error = mocker.patch(
            'bitmex_websocket.BitMEXWebsocket.on_error')
        socket = BitMEXWebsocket()
        message = {
            "success": "true",
            "subscribe": "instrument:XBTH17",
            "request": {
                "op": "subscribe",
                "args": ["instrument:XBTH17"]
            }
        }
        subscribe_handler = mocker.stub()
        socket.on('subscribe', subscribe_handler)
        socket.emit('subscribe', message)

        error.assert_not_called()
        subscribe_handler.assert_called_once_with(message)

    def test_on_subscribe_called_on_sub_error_message(self, mocker):
        """
        on_message should call on_subscribe when subscription error is received
        """
        error = mocker.patch(
            'bitmex_websocket.BitMEXWebsocket.on_error')
        socket = BitMEXWebsocket()
        message = {
            "status": 400,
            "error": "Unknown table: instrument_",
            "meta": {},
            "request": {
                "op": "subscribe",
                "args": ["instrument_:XBTH17"]
            }
        }

        socket.on_message(socket, json.dumps(message))
        error.assert_called_with("Unknown table: instrument_")


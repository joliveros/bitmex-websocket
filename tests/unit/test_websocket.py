from bitmex_websocket.websocket import BitMEXWebsocket
from tests import *
from tests.helpers import *
import pytest


def test_connect_should_connect_ws(mocker):
    connect_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')

    socket = BitMEXWebsocket()
    socket.connect()

    connect_websocket.assert_called_once()


def test_build_websocket_url(mocker):
    socket = BitMEXWebsocket()
    url = socket.build_websocket_url('https://testnet.bitmex.com/api/v1/')

    assert url == 'wss://testnet.bitmex.com/realtime'


@pytest.mark.xfail
def test_should_fail(self):
    self.assertEqual(False, True)

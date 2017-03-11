from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
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


def test_build_websocket_url_w_heartbeat(mocker):
    socket = BitMEXWebsocket()
    socket.heartbeatEnabled = True
    url = socket.build_websocket_url('https://testnet.bitmex.com/api/v1/')

    assert url == 'wss://testnet.bitmex.com/realtime?heartbeat=true'


def test_build_websocket_url_without_heartbeat(mocker):
    socket = BitMEXWebsocket()
    socket.heartbeatEnabled = False
    url = socket.build_websocket_url('https://testnet.bitmex.com/api/v1/')

    assert url == 'wss://testnet.bitmex.com/realtime'


def test_subscribe_to_channel(mocker):
    send_message = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.send_message')
    socket = BitMEXWebsocket()
    socket.symbol = 'test_symbol'
    socket.heartbeatEnabled = False
    socket.subscribe('test_channel')

    send_message.assert_called_with(
        {'op': 'subscribe', 'args': ['test_channel:test_symbol']})


@pytest.mark.xfail
def test_should_fail(self):
    self.assertEqual(False, True)

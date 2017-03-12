from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
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


def test_connect_websocket_with_heartbeat(mocker):
    '''
    Ensure heartbeat is enabled on the websocket.
    '''
    websocket_run_forever = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.websocket_run_forever')
    init_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.init_websocket')
    socket = BitMEXWebsocket()
    socket.shouldAuth = False
    socket.heartbeatEnabled = True
    socket.connect_websocket()

    websocket_run_forever.assert_called_with(
        {'ping_timeout': 10, 'ping_interval': 25})
    init_websocket.assert_called_once()


def test_connect_websocket_without_heartbeat(mocker):
    '''
    Ensure heartbeat is disabled on the websocket.
    '''
    websocket_run_forever = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.websocket_run_forever')
    init_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.init_websocket')
    socket = BitMEXWebsocket()
    socket.shouldAuth = False
    socket.heartbeatEnabled = False
    socket.connect_websocket()

    # neither ping_timeout or ping_interval are passed as args
    websocket_run_forever.assert_called_with({})
    init_websocket.assert_called_once()


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

from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
from builtins import *
from bitmex_websocket.websocket import BitMEXWebsocket
from tests.helpers import message_fixtures
import pytest
import time
import json
import ssl

orderBookL2_data = message_fixtures()['orderBookL2']


def test_connect_should_connect_ws(mocker):
    connect_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')

    socket = BitMEXWebsocket()
    socket.connect()

    connect_websocket.assert_called_once()


def test_build_websocket_url_w_heartbeat(mocker):
    connect_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')
    socket = BitMEXWebsocket()
    socket.heartbeatEnabled = True
    url = socket.build_websocket_url('https://testnet.bitmex.com/api/v1/')

    assert url == 'wss://testnet.bitmex.com/realtime?heartbeat=true'


def test_build_websocket_url_without_heartbeat(mocker):
    connect_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')
    socket = BitMEXWebsocket()
    socket.heartbeatEnabled = False

    url = socket.build_websocket_url('https://testnet.bitmex.com/api/v1/')

    assert url == 'wss://testnet.bitmex.com/realtime'


def test_on_message_receive_ping(mocker):
    """
    Bitmex websocket uses Primus websocket lib which uses the
    following heartbeat scheme:

          client will disconnect
            if not recv within
              `pingTimeout`

         primus::pong::{timestamp}
        +----------------------+
        |                      |
    +---v----+            +---------+
    | server |            |  client |
    +--------+            +----^----+
        |                      |
        +----------------------+
         primus::ping::{timestamp}

          sent at `pingInterval`
          server will disconnect
          if no response since
               last ping
    """
    connect_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')
    send_message_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.send_message')
    socket = BitMEXWebsocket()
    ping_handler = mocker.stub()
    socket.on('ping', ping_handler)
    latency_handler = mocker.stub()
    socket.on('latency', latency_handler)

    ping_message = "primus::ping::%s" % (time.time() * 1000)
    socket.on_message(ping_message)
    ping_handler.assert_called_once_with(ping_message)
    latency_handler.assert_called_once()


def test_connect_websocket_with_heartbeat(mocker):
    '''
    Ensure heartbeat is enabled on the websocket.
    '''
    websocket_run_forever = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.websocket_run_forever')
    init_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.init_websocket')
    wait_for_connection = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.wait_for_connection')
    socket = BitMEXWebsocket()
    socket.shouldAuth = False
    socket.heartbeatEnabled = True
    socket.connect_websocket()

    websocket_run_forever.assert_called_with({
        'sslopt': {"cert_reqs": ssl.CERT_NONE},
        'ping_timeout': 20,
        'ping_interval': 60
    })
    init_websocket.assert_called_once()
    wait_for_connection.assert_called_once()


def test_connect_websocket_without_heartbeat(mocker):
    '''
    Ensure heartbeat is disabled on the websocket.
    '''
    websocket_run_forever = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.websocket_run_forever')
    init_websocket = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.init_websocket')
    wait_for_connection = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.wait_for_connection')
    socket = BitMEXWebsocket()
    socket.shouldAuth = False
    socket.heartbeatEnabled = False
    socket.connect_websocket()

    # neither ping_timeout or ping_interval are passed as args
    websocket_run_forever.assert_called_with({'sslopt': {"cert_reqs": ssl.CERT_NONE}})
    init_websocket.assert_called_once()
    wait_for_connection.assert_called_once()


def test_re_connect_on_error(mocker):
    '''
    Ensure heartbeat is disabled on the websocket.
    '''
    connect_websocket_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect_websocket')
    socket = BitMEXWebsocket()
    socket.shouldAuth = False
    socket.heartbeatEnabled = False

    socket.re_connect()

    connect_websocket_mock.assert_called_once()


def test_subscribe_to_channel(mocker):
    socket = BitMEXWebsocket()
    socket.heartbeatEnabled = False
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
    socket.on_message(json.dumps(message))
    handler.assert_called_once()


def test_subscribe_instrument_on_message(mocker):
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
    # socket.on('subscribe', subscribe_handler)

    @socket.on('subscribe')
    def handler(message):
        subscribe_handler(message)
    socket.on_message(json.dumps(message))

    subscribe_handler.assert_called_once_with(message)


def test_on_subscribe_success(mocker):
    error = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.error')
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


def test_subscribe_action_handler(mocker):
    """
    When calling BitMEXWebsocket.subscribe_action(), ensure a proper subscriptionMsg
    message is sent and a subscription event is received when the channel is
    subscribed.
    """
    send_message_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.send_message')
    on_subscribe_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.on_subscribe')
    socket = BitMEXWebsocket()
    message = {
        "success": "true",
        "subscribe": "instrument:XBTH17",
        "request": {
            "op": "subscribe",
            "args": ["instrument:XBTH17"]
        }
    }
    partial_action_handler = mocker.stub()
    socket.subscribe_action('partial',
                            'orderBookL2',
                            'XBTH17',
                            partial_action_handler)
    socket.on_message(json.dumps(message))
    send_message_mock.assert_called_once()
    on_subscribe_mock.assert_called_once()
    partial_message = orderBookL2_data['partial']
    socket.on_message(json.dumps(partial_message))
    partial_action_handler.assert_called_once_with(partial_message)


def test_on_subscribe_called_on_sub_error_message(mocker):
    '''
    on_message should call on_subscribe when subscription error is received
    '''
    error = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.error')
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

    socket.on_message(json.dumps(message))
    error.assert_called_with("Unknown table: instrument_")


def test_on_partial_action_message_data(mocker):
    socket = BitMEXWebsocket()
    message = orderBookL2_data['partial']
    partial_event_handler = mocker.stub()
    event_name = socket.gen_action_event_key(
                            message['action'],
                            message['data'][0]['symbol'],
                            message['table'])
    socket.on(event_name, partial_event_handler)
    socket.on_message(json.dumps(message))

    partial_event_handler.assert_called_once_with(message)


def test_on_action_triggers_events(mocker):
    socket = BitMEXWebsocket()

    message = orderBookL2_data['partial']
    price_level = message['data'][0]
    mock_event_handler = mocker.stub(name='on_order_book_partial_handler')
    partial_event_name = socket.gen_action_event_key(
        price_level['symbol'],
        message['table'],
        message['action'],)

    socket.on(partial_event_name, mock_event_handler)
    socket.emit(partial_event_name, message)
    mock_event_handler.assert_called_with(message)

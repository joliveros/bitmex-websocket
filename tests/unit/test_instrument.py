from __future__ import (absolute_import,
                        division,
                        print_function,
                        unicode_literals)
from builtins import *
from bitmex_websocket import Instrument
from tests.helpers import message_fixtures
import pytest
import json
import time
from time import sleep

fixtures = message_fixtures()
orderBookL2_data = fixtures['orderBookL2']
instrument_data = fixtures['instrument']


def test_average_latency(mocker):
    """
    The BitMEXWebsocket emits 'latency' events every time a 'ping'
    comes in. This allows for a calculation for message latency.

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
    init_mock = mocker.patch(
        'bitmex_websocket.Instrument.init')

    instrument = Instrument(shouldAuth=True)

    latency_handler = mocker.stub()
    instrument.on('latency', latency_handler)
    # some time elapses and the ping message is received
    instrument.on_latency(100)
    latency_handler.assert_called_once()
    instrument.get_latency()


def test_on_partial_action_instrument_data(mocker):
    init_mock = mocker.patch(
        'bitmex_websocket.Instrument.init')

    instrument = Instrument()
    partial_message = instrument_data['partial']

    instrument.on_action(partial_message)

    assert instrument.data['instrument']


def test_on_update_action_instrument_data(mocker):
    init_mock = mocker.patch(
        'bitmex_websocket.Instrument.init')
    partial_message = instrument_data['partial']
    update_message = instrument_data['update']

    instrument = Instrument()

    instrument.on_action(partial_message)
    assert instrument.data['instrument']

    instrument.on_action(update_message)

    updated_instrument_table = instrument.get_table('instrument')
    assert updated_instrument_table['impactAskPrice'] \
        == update_message['data'][0]['impactAskPrice']


def test_on_partial_orderBookL2_action_data(mocker):
    init_mock = mocker.patch(
        'bitmex_websocket.Instrument.init')
    instrument = Instrument()

    message = orderBookL2_data['partial']

    instrument.on_action(message)

    assert instrument.data['orderBookL2']


def test_on_orderBookL2_action_data(mocker):
    """
    Ensure orderBookL2 is updated on delete, insert and update actions.
    """
    init_mock = mocker.patch(
        'bitmex_websocket.Instrument.init')
    instrument = Instrument()

    # Recieve partial action message
    partial_action_message = orderBookL2_data['partial']
    partial_data = partial_action_message['data']
    instrument.on_action(partial_action_message)
    table = 'orderBookL2'
    for partial_level in partial_data:
        level = next(level for level in instrument.get_table(table)
                     if level['id'] == partial_level['id'])
        assert level

    # Receive delete action message
    delete_action_message = orderBookL2_data['delete']
    delete_level_id = delete_action_message['data'][0]['id']

    instrument.on_action(delete_action_message)
    delete_level = next((level for level in instrument.get_table(table)
                        if level['id'] == delete_level_id), None)
    assert not delete_level

    # Receive insert action message
    insert_action_message = orderBookL2_data['insert']
    instrument.on_action(insert_action_message)
    insert_data = insert_action_message['data']

    for insert_level in insert_data:
        level = next(level for level in instrument.get_table(table)
                     if level['id'] == insert_level['id'])
        assert level

    # Receive update action message
    update_action_message = orderBookL2_data['update']
    update_data = update_action_message['data']
    level_update = update_data[0]
    instrument.on_action(update_action_message)
    updated_level = next(level for level in instrument.get_table(table)
                         if level['id'] == level_update['id'])

    assert updated_level['size'] == level_update['size']

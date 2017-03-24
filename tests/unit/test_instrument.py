from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
from builtins import *
from bitmex_websocket import Instrument
from tests import *
from tests.helpers import *
import pytest
import json


orderBookL2_data = {}
with open('./tests/fixtures/order_book_l2_partial_action_message.json')\
        as partial_data:
    orderBookL2_data['partial'] = json.load(partial_data)
with open('./tests/fixtures/order_book_l2_insert_action_message.json')\
        as insert_data:
    orderBookL2_data['insert'] = json.load(insert_data)
with open('./tests/fixtures/order_book_l2_delete_action_message.json')\
        as delete_data:
    orderBookL2_data['delete'] = json.load(delete_data)
with open('./tests/fixtures/order_book_l2_update_action_message.json')\
        as update_data:
    orderBookL2_data['update'] = json.load(update_data)


def test_init(mocker):
    connect_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_to_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_channels')
    subscribe_to_secure_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_secure_channels')
    Instrument()

    connect_mock.assert_called_once()
    subscribe_to_channels_mock.assert_called_once()
    subscribe_to_secure_channels_mock.assert_not_called()


def test_subscribe_to_channels(mocker):
    connect_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_to_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_channels')
    subscribe_to_secure_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_secure_channels')
    Instrument(shouldAuth=True)

    connect_mock.assert_called_once()
    subscribe_to_channels_mock.assert_called_once()
    subscribe_to_secure_channels_mock.assert_called_once()


def test_subscribe_to_public_channels_only(mocker):
    connect_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_to_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_channels')
    subscribe_to_secure_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_secure_channels')
    Instrument(shouldAuth=False)

    connect_mock.assert_called_once()
    subscribe_to_channels_mock.assert_called_once()
    subscribe_to_secure_channels_mock.assert_not_called()


def test_on_partial_action_instrument_data(mocker):
    connect_mock = mocker.patch(
        'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_mock = mocker.patch('bitmex_websocket.BitMEXWebsocket.subscribe')
    instrument = Instrument()
    with open('./tests/fixtures/instrument_partial_action_message.json')\
            as message_data:
        message = json.load(message_data)

        instrument.on_partial(message)

        assert instrument.data['instrument']


def test_on_partial_orderBookL2_action_data(mocker):
    instrument = Instrument()

    message = orderBookL2_data['partial']

    instrument.on_partial(message)

    assert instrument.data['orderBookL2']


def test_on_orderBookL2_action_data(mocker):
    """
    Ensure orderBookL2 is updated on delete, insert and update actions.
    """
    instrument = Instrument()

    # Recieve partial action message
    partial_action_message = orderBookL2_data['partial']
    partial_data = partial_action_message['data']
    instrument.on_partial(partial_action_message)
    for partial_level in partial_data:
        level = next(level for level in instrument.data['orderBookL2']
                     if level['id'] == partial_level['id'])
        assert level

    # Receive delete action message
    delete_action_message = orderBookL2_data['delete']
    delete_level_id = delete_action_message['data'][0]['id']

    instrument.on_delete(delete_action_message)
    delete_level = next((level for level in partial_data
                        if level['id'] == delete_level_id), None)
    assert not delete_level

    # Receive insert action message
    insert_action_message = orderBookL2_data['insert']
    instrument.on_insert(insert_action_message)
    insert_data = insert_action_message['data']

    for insert_level in insert_data:
        level = next((level for level in instrument.data['orderBookL2']
                     if level['id'] == insert_level['id']), None)
        assert level

    # Receive update action message
    update_action_message = orderBookL2_data['update']
    update_data = update_action_message['data']
    level_update = update_data[0]
    instrument.on_update(update_action_message)
    updated_level = next(level for level in instrument.data['orderBookL2']
                         if level['id'] == level_update['id'])

    assert updated_level['size'] == level_update['size']


def test_getTable(mocker):
    """
    Ensure getTable('orderBookL2') returns the latest orderbook.
    """
    connect_mock = mocker.patch(
    'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_to_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_channels')
    subscribe_to_secure_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_secure_channels')
    instrument = Instrument()
    # Recieve partial action message
    partial_action_message = orderBookL2_data['partial']
    partial_data = partial_action_message['data']
    instrument.on_partial(partial_action_message)
    orderBookL2 = instrument.getTable('orderBookL2')
    assert orderBookL2 == partial_action_message['data']


def test_emit_event_on_partial_table_action(mocker):
    """
    Ensure table change and action events are called on partial action.
    """
    connect_mock = mocker.patch(
    'bitmex_websocket.websocket.BitMEXWebsocket.connect')
    subscribe_to_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_channels')
    subscribe_to_secure_channels_mock = mocker.patch(
        'bitmex_websocket.Instrument.subscribe_to_secure_channels')
    instrument = Instrument()
    orderBookL2_change = mocker.stub()
    instrument.on('orderBookL2', orderBookL2_change)
    # Recieve partial action message
    partial_action_message = orderBookL2_data['partial']
    partial_data = partial_action_message['data']
    instrument.on_partial(partial_action_message)
    orderBookL2 = instrument.getTable('orderBookL2')
    assert orderBookL2 == partial_action_message['data']
    # Ensure orderBookL2 event was emitted
    orderBookL2_change.assert_called_once_with(orderBookL2)

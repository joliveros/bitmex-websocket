from __future__ import (absolute_import,
                        division,
                        print_function,
                        unicode_literals)
from builtins import *

from websocket import WebSocketConnectionClosedException, \
    WebSocketTimeoutException, WebSocketException

from bitmex_websocket import constants
from bitmex_websocket._bitmex_websocket import BitMEXWebsocket
from pyee import EventEmitter
import json
import alog

__all__ = ['Instrument']


class Instrument(BitMEXWebsocket):
    def __init__(self,
                 symbol='XBTH17',
                 channels=None,
                 should_auth=False,
                 max_table_length=constants.MAX_TABLE_LEN):

        BitMEXWebsocket.__init__(self, should_auth)

        self.secure_channels = []

        if channels is None:
            channels = []
        self.channels = channels

        if max_table_length > 0:
            self.max_table_length = max_table_length
        else:
            self.max_table_length = constants.MAX_TABLE_LEN

        self.symbol = symbol

        self.data = {
            'orderBookL2': [],
            'instrument': []
        }

    def connect(self):
        self.on('open', self._subscribe_channels)
        super().connect()

    def _subscribe_channels(self):
        self.subscribe_to_channels()
        self.subscribe_to_instrument_channels()

        if self.should_auth:
            self.subscribe_to_secure_instrument_channels()

    def subscribe_to_channels(self):
        channels = self.channels
        # Subscribe to all channels by default
        for channel in constants.CHANNELS:
            if len(channels) > 0 and channel not in channels:
                channel = None

            if channel:
                handler_name = "on_%s" % (channel)
                handler = {}
                if hasattr(self, handler_name):
                    handler = getattr(self, handler_name)
                else:
                    handler = self.on_channel

                self.subscribe(channel, handler)

    def subscribe_to_secure_channels(self):
        channels = self.channels

        # Subscribe to all channels by default
        for channel in constants.SECURE_CHANNELS:
            if len(channels) > 0 and channel not in channels:
                channel = None

            if channel:
                handler_name = "on_%s" % (channel)
                handler = {}
                if hasattr(self, handler_name):
                    handler = getattr(self, handler_name)
                else:
                    handler = self.on_channel

                self.subscribe(channel, handler)

    def subscribe_to_instrument_channels(self):
        channels = self.channels
        symbol = self.symbol

        # Subscribe to all channels by default
        for channel in constants.INSTRUMENT_CHANNELS:
            if len(channels) > 0 and channel not in channels:
                channel = None

            if channel:
                self.subscribe_actions_for_channel(channel, symbol)

    def subscribe_to_secure_instrument_channels(self):
        channels = self.channels
        symbol = self.symbol

        # Subscribe to all channels by default
        for channel in constants.SECURE_INSTRUMENT_CHANNELS:
            if len(channels) > 0 and channel not in channels:
                channel = None

            if channel:
                self.subscribe_actions_for_channel(channel, symbol)

    def subscribe_actions_for_channel(self, channel, symbol):
        for action in constants.ACTIONS:
            handler_name = "on_%s" % (channel)
            handler = {}
            if hasattr(self, handler_name):
                handler = getattr(self, handler_name)
            else:
                handler = self.on_action

            self.subscribe_action(action,
                                            channel,
                                            symbol,
                                            handler)

    def on_subscribe(self, channel):
        self.channels.append(channel)

    def all_channels(self):
        allChannels = []
        for channel in self.channels:
            allChannels.append(channel)

        for channel in self.secure_channels:
            allChannels.append(channel)

        return allChannels

    def on_channel(self, message):
        alog.debug("#on_channel")
        alog.debug(message)
        for item in message['data']:
            self.prepend_to_table(message['table'], item)

    def on_action(self, message):
        self.emit('action', message)
        return
        table = message['table']
        data = message['data']
        alog.debug("on_action")
        action = message['action']

        if action == 'delete':
            for item in data:
                self.delete_from_table(table, item)
        elif action == 'update' and 'id' in data[0]:
            for item in data:
                self.update_item_in_table(table, item)
        elif action == 'partial' and 'id' not in data[0]:
            self.data[table] = data[0]
        elif action == 'insert' and 'id' not in data[0]:
            self.update_keys_in_table(table, data[0])
        elif action == 'partial' or action == 'insert':
            for item in data:
                self.prepend_to_table(table, item)
        else:
            self.update_keys_in_table(table, data[0])

        self.emit(table, table, self.get_table(table))

    def update_keys_in_table(self, table, update):
        self.data[table].update(update)

    def delete_from_table(self, table, item):
        alog.debug('#delete_from_table:%s' % (table))
        alog.debug(item)
        if table not in self.data:
            self.data[table] = []
        delete_item = next(_item for _item in self.data['orderBookL2']
                           if _item['id'] == item['id'])
        if delete_item:
            self.data[table].remove(delete_item)

    def prepend_to_table(self, table, item):
        if table not in self.data:
            self.data[table] = []
        isMaxLength = len(self.data[table]) == self.max_table_length
        if isMaxLength and 'orderBook' not in table:
            self.data[table].pop()

        self.data[table].insert(0, item)
        alog.debug('#prepend_to_table')
        alog.debug(self.data[table])

    def update_item_in_table(self, table, update):
        alog.debug("# update_item_in_table")
        alog.debug(json.dumps(update))

        item_to_update = next(item for item in self.data[table]
                              if item['id'] == update['id'])

        item_to_update.update(update)

    def get_table(self, table):
        return self.data[table]

    def update_instrument(self, action, data):
        alog.debug(data)
        self.data['instrument'] = data[0]

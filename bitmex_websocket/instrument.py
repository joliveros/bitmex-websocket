from __future__ import (absolute_import,
                        division,
                        print_function,
                        unicode_literals)
from builtins import *
from bitmex_websocket import constants
from bitmex_websocket.websocket import BitMEXWebsocket
from pyee import EventEmitter
import json
import alog

__all__ = ['Instrument']


class Instrument(EventEmitter):
    def __init__(self,
                 symbol='XBTH17',
                 channels=[],
                 shouldAuth=False,
                 maxTableLength=constants.MAX_TABLE_LEN,
                 websocket=None):

        EventEmitter.__init__(self)
        self.channels = channels

        if maxTableLength > 0:
            self.maxTableLength = maxTableLength
        else:
            self.maxTableLength = constants.MAX_TABLE_LEN

        self.shouldAuth = shouldAuth
        self.symbol = symbol
        self.websocket = websocket

        self.data = {
            'orderBookL2': [],
            'instrument': []
        }

        self.init()

    def init(self, reset=False):
        alog.debug("## init")
        channels = self.channels
        symbol = self.symbol
        shouldAuth = self.shouldAuth
        websocket = self.websocket

        if reset:
            websocket = self.websocket = BitMEXWebsocket()

        if not websocket:
            self.websocket = BitMEXWebsocket()

        self.websocket.connect(
           shouldAuth=shouldAuth,
           websocket=websocket
        )

        self.websocket.on('subscribe', self.on_subscribe)
        self.websocket.on('latency', self.on_latency)
        self.channels = []
        self.subscribe_to_channels(channels)
        self.subscribe_to_instrument_channels(symbol, channels)
        self.secureChannels = []
        if shouldAuth:
            self.subscribe_to_secure_instrument_channels(symbol, channels)

    def on_latency(self, message):
        alog.debug("# on_latency")
        alog.debug(message)

        latency = []
        if 'latency' not in self.data:
            self.data['latency'] = []

        if len(self.data['latency']) > self.maxTableLength - 1:
            self.data['latency'].pop()

        latency.append(message)

        self.data['latency'] = latency

        # calculate average latency
        avg_latency = sum(latency)/len(latency)
        self.emit('latency', avg_latency)
        alog.debug("## avg latency: %s" % (avg_latency))

    def get_latency(self):
        return self.data['latency']

    def subscribe_to_channels(self, channels):
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

                self.websocket.subscribe(channel, handler)

    def subscribe_to_secure_channels(self, channels):
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

                self.websocket.subscribe(channel, handler)

    def subscribe_to_instrument_channels(self, symbol, channels):
        # Subscribe to all channels by default
        for channel in constants.INSTRUMENT_CHANNELS:
            if len(channels) > 0 and channel not in channels:
                channel = None

            if channel:
                self.subscribe_actions_for_channel(channel, symbol)

    def subscribe_to_secure_instrument_channels(self, symbol, channels):
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

            self.websocket.subscribe_action(action,
                                            channel,
                                            symbol,
                                            handler)

    def on_subscribe(self, channel):
        self.channels.append(channel)

    def all_channels(self):
        allChannels = []
        for channel in self.channels:
            allChannels.append(channel)

        for channel in self.secureChannels:
            allChannels.append(channel)

        return allChannels

    def on_channel(self, message):
        alog.debug("#on_channel")
        alog.debug(message)
        for item in message['data']:
            self.prepend_to_table(message['table'], item)

    def on_action(self, message):
        self.emit('action', message)
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
        isMaxLength = len(self.data[table]) == self.maxTableLength
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

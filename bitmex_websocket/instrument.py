from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import sys
import threading
import traceback
from time import sleep
import json
import decimal
from bitmex_websocket.settings import settings
from bitmex_websocket.utils.log import setup_custom_logger
from bitmex_websocket.websocket import BitMEXWebsocket
from pyee import EventEmitter

# Don't grow a table larger than this amount. Helps cap memory usage.
MAX_TABLE_LEN = 200
CHANNELS = [
    'chat',          # Trollbox chat
    'connected',     # Statistics of connected users/bots
    'instrument',    # Instrument updates including turnover and bid/ask
    'insurance',     # Daily Insurance Fund updates
    'liquidation',   # Liquidation orders as they're entered into the book
    'orderBookL2',   # Full level 2 orderBook
    'orderBook10',   # Top 10 levels using traditional full book push
    'publicNotifications',  # System-wide notifications
    'quote',         # Top level of the book
    'quoteBin1m',    # 1-minute quote bins
    'settlement',    # Settlements
    'trade',         # Live trades
    'tradeBin1m',    # 1-minute ticker bins
]

SECURE_CHANNELS = [
    'affiliate',   # Affiliate status, such as total referred users & payout %
    'execution',   # Individual executions; can be multiple per order
    'order',       # Live updates on your orders
    'margin',      # Updates on your current account balance and margin requirements
    'position',    # Updates on your positions
    'privateNotifications',  # Individual notifications - currently not used
    'transact'     # Deposit/Withdrawal updates
    'wallet'       # Bitcoin address balance data, including total deposits & withdrawals
]

# Actions that might be received for each table
ACTIONS = ('partial', 'insert', 'update', 'delete')


class Instrument(EventEmitter):
    def __init__(self,
                 symbol='XBTH17',
                 channels=None,
                 secureChannels=None,
                 shouldAuth=False,
                 websocket=None):

        EventEmitter.__init__(self)
        self.symbol = symbol
        self.shouldAuth = shouldAuth
        self.data = {
            'orderBookL2': [],
            'instrument': []
        }

        self.websocket = BitMEXWebsocket()
        self.websocket.connect(
           shouldAuth,
           websocket
        )

        self.websocket.on('subscribe', self.on_subscribe)
        self.channels = []
        self.subscribe_to_channels(symbol, channels)
        self.secureChannels = []
        if shouldAuth:
            self.subscribe_to_secure_channels(symbol, secureChannels)
        self.logger = setup_custom_logger("instrument:%s" % (symbol))

    def subscribe_to_channels(self, symbol, channels):
        # Subscribe to all channels by default
        if not channels:
            _channels = CHANNELS
        else:
            _channels = channels

        for channel in _channels:
            self.subscribe_actions_for_channel(symbol, channel)

    def subscribe_to_secure_channels(self, symbol, channels):
        # Subscribe to all channels by default
        if not channels:
            _channels = SECURE_CHANNELS
        else:
            _channels = channels

        for channel in _channels:
            self.subscribe_actions_for_channel(symbol, channel)

    def subscribe_actions_for_channel(self, channel, symbol):
        for action in ACTIONS:
            self.websocket.subscribe(action,
                                     channel,
                                     symbol,
                                     getattr(self, "on_%s" % (action)))

    def on_subscribe(self, channel):
        self.channels.append(channel)

    def all_channels(self):
        allChannels = []
        for channel in self.channels:
            allChannels.append(channel)

        for channel in self.secureChannels:
            allChannels.append(channel)

        return allChannels

    def on_partial(self, message):
        table = message['table']
        data = message['data']
        self.logger.debug("%s: partial" % table)
        getattr(self, "update_%s" % (table))('partial', data)

    def on_action(self, table, handler):
        for action in ACTIONS:
            self.websocket.subscribe(action,
                                     table,
                                     self.symbol,
                                     handler)

    def on_insert(self, message):
        table = message['table']
        action = message['action']
        self.logger.debug('%s: inserting' % (table))
        if table == 'orderBookL2':
            return self.update_orderBookL2(action, message['data'])

        self.data[table] += message['data']

        # Limit the max length of the table to avoid excessive memory
        # usage. Don't trim orders because we'll lose valuable state if
        # we do.
        max_len = BitMEXWebsocket.MAX_TABLE_LEN
        if table != 'order' and len(self.data[table]) > max_len:
            self.data[table] = self.data[table][(max_len // 2):]

    def on_update(self, message):
        table = message['table']
        action = message['action']
        self.logger.debug('%s: updating' % (table))
        if table == 'orderBookL2':
            return self.update_orderBookL2(action, message['data'])

        # Locate the item in the collection and update it.
        for updateData in message['data']:
            item = findItemByKeys(self.keys[table], self.data[table], updateData)
            if not item:
                return  # No item found to update. Could happen before push

            # Log executions
            is_canceled = 'ordStatus' in updateData and updateData['ordStatus'] == 'Canceled'
            if table == 'order' and 'leavesQty' in updateData and not is_canceled:
                instrument = self.get_instrument(item['symbol'])
                contExecuted = abs(item['leavesQty'] - updateData['leavesQty'])
                self.logger.info("Execution: %s %d Contracts of %s at %.*f" %
                                 (item['side'], contExecuted, item['symbol'],
                                  instrument['tickLog'], item['price']))

            item.update(updateData)
            # Remove cancelled / filled orders
            if table == 'order' and item['leavesQty'] <= 0:
                self.data[table].remove(item)

    def on_delete(self, message):
        table = message['table']
        action = message['action']
        self.logger.debug('%s: deleting %s' % (table, message['data']))
        if table == 'orderBookL2':
            return self.update_orderBookL2(action, message['data'])
        # Locate the item in the collection and remove it.
        for deleteData in message['data']:
            item = findItemByKeys(self.keys[table], self.data[table], deleteData)
            self.data[table].remove(item)

    def update_orderBookL2(self, method, data):
        self.logger.debug("update method: %s" % (method))
        self.logger.debug(json.dumps(data))
        if method == 'partial':
            self.data['orderBookL2'] = data
            self.emit('orderBookL2', self.data['orderBookL2'])
        elif method == 'delete':
            for delete in data:
                level = next(level for level in self.data['orderBookL2']
                             if level['id'] == delete['id'])
                if level:
                    self.logger.debug("delete level %s" % (json.dumps(level)))
                    self.data['orderBookL2'].remove(level)
        elif method == 'insert':
            for level in data:
                self.logger.debug("insert level %s" % (json.dumps(level)))
                self.data['orderBookL2'].append(level)
            self.emit('orderBookL2', self.data['orderBookL2'])
        elif method == 'update':
            for update in data:
                level = next(level for level in self.data['orderBookL2']
                             if level['id'] == update['id'])
                self.logger.debug("update level %s" % (json.dumps(level)))
                level['size'] = update['size']
            self.emit('orderBookL2', self.data['orderBookL2'])


    def update_instrument(self, action, data):
        self.logger.debug(data)
        self.data['instrument'] = data[0]

    def getTable(self, table):
        return self.data[table]

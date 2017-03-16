from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import sys
import websocket
import threading
import traceback
from time import sleep
import json
import decimal
import logging
from bitmex_websocket.settings import settings
from bitmex_websocket.utils.log import setup_custom_logger
from bitmex_websocket.auth.APIKeyAuth import generate_nonce, generate_signature
from future.utils import iteritems
from urllib.parse import urlparse


# The Websocket offers a bunch of data as raw properties right on the object.
# On connect, it synchronously asks for a push of all this data then returns.
# Right after, the MM can start using its data. It will be updated in realtime,
# so the user can poll as often as it wants.
class BitMEXWebsocket():

    # Don't grow a table larger than this amount. Helps cap memory usage.
    MAX_TABLE_LEN = 200

    def __init__(self):
        self.logger = setup_custom_logger('BitMEXWebsocket')
        self.__reset()

    def connect(
            self,
            symbol="XBTH17",
            shouldAuth=False,
            websocket=None,
            heartbeatEnabled=True):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting WebSocket.")
        self.symbol = symbol
        self.shouldAuth = shouldAuth
        self.heartbeatEnabled = heartbeatEnabled
        self.connect_websocket()

        self.logger.info('Connected to WS. Waiting for data images, this may \
        take a moment...')

    def build_websocket_url(self, base_url=settings.BASE_URL):
        self.logger.debug('Build websocket url from: %s' % (base_url))

        urlParts = list(urlparse(base_url))
        queryString = ''
        if self.heartbeatEnabled:
            queryString = '?heartbeat=true'

        url = "wss://{}/realtime{}".format(urlParts[1], queryString)
        self.logger.debug(url)
        return url

    def connect_websocket(self):
        """Connect to the websocket in a thread."""

        self.logger.debug("Starting thread")
        self.init_websocket()

        # setup websocket.run_forever arguments
        wsRunArgs = {}
        if self.heartbeatEnabled:
            wsRunArgs['ping_timeout'] = 10
            wsRunArgs['ping_interval'] = 25

        self.logger.debug("websocket.run_forever: %s" % (wsRunArgs))

        # Run the websocket on another thread and enable heartbeat
        self.wst = threading.Thread(
            target=lambda: self.websocket_run_forever(wsRunArgs)
        )
        self.wst.daemon = True
        self.wst.start()
        self.logger.info("Started thread")
        self.wait_for_connection()

    def wait_for_connection(self):
       # Wait for connect before continuing
        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) \
                and conn_timeout and not self._error:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            self.logger.error("Couldn't connect to WS! Exiting.")
            self.exit()
            sys.exit(1)

    def init_websocket(self):
        wsURL = self.build_websocket_url()
        self.logger.debug("Connecting to %s" % (wsURL))
        self.ws = websocket.WebSocketApp(
            wsURL,
            on_message=self.on_message,
            on_close=self.__on_close,
            on_open=self.__on_open,
            on_error=self.__on_error,
            # We can login using
            #  email/pass or API key
            header=self.__get_auth())

    def websocket_run_forever(self, args):
        self.ws.run_forever(**args)

    def subscribe(self, channel):
        channel = "{}:{}".format(channel, self.symbol)
        subscriptionMsg = {"op": "subscribe", "args": [channel]}

        self.logger.info(subscriptionMsg)
        self.send_message(subscriptionMsg)

    def send_message(self, message):
        self.ws.send(json.dumps(message))

    #
    # Lifecycle methods
    #
    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()

    #
    # Private methods
    #
    def is_connected(self):
        self.ws.sock.connected

    def __get_auth(self):
        '''Return auth headers. Will use API Keys if present in settings.'''

        if self.shouldAuth is False:
            return []

        self.logger.info("Authenticating with API Key.")
        # To auth to the WS using an API key, we generate a signature
        # of a nonce and the WS API endpoint.
        self.logger.debug(settings.BITMEX_API_KEY)
        nonce = generate_nonce()
        api_signature = generate_signature(
            settings.BITMEX_API_SECRET, 'GET', '/realtime', nonce, '')
        return [
            "api-nonce: " + str(nonce),
            "api-signature: " + api_signature,
            "api-key:" + settings.BITMEX_API_KEY
        ]

    def __wait_for_account(self):
        '''On subscribe, this data will come down. Wait for it.'''
        # Wait for the keys to show up from the ws
        while not {'margin', 'position', 'order'} <= set(self.data):
            sleep(0.1)

    def __wait_for_symbol(self, symbol):
        '''On subscribe, this data will come down. Wait for it.'''
        while not {'instrument', 'trade', 'quote'} <= set(self.data):
            sleep(0.1)

    def __send_command(self, command, args=[]):
        '''Send a raw command.'''
        self.ws.send(json.dumps({"op": command, "args": args}))

    def on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        self.logger.debug(json.dumps(message, indent=4, sort_keys=True))

        action = message['action'] if 'action' in message else None

        try:
            if 'subscribe' in message:
                self.on_subscribe(message)
            elif 'status' in message:
                self.on_status(message)
            elif action:
                self.on_action(action, message)
        except:
            self.logger.error(traceback.format_exc())

    def on_subscribe(self, message):
        if message['success']:
            self.logger.debug("Subscribed to %s." % message['subscribe'])
        else:
            self.error("Unable to subscribe to %s. Error: \"%s\" Please\
            check and restart." % (
                message['request']['args'][0], message['error']))

    def on_status(self, message):
        if message['status'] == 400:
            self.error(message['error'])
        if message['status'] == 401:
            self.error("API Key incorrect, please check and restart.")

    def on_action(self, action, message):
        table = message['table'] if 'table' in message else None

        if table not in self.data:
            self.data[table] = []

        if table not in self.keys:
            self.keys[table] = []

        # There are four possible actions from the WS:
        # 'partial' - full table image
        # 'insert'  - new row
        # 'update'  - update row
        # 'delete'  - delete row
        if action == 'partial':
            self.logger.debug("%s: partial" % table)
            # Keys are communicated on partials to let you know how to uniquely
            # identify an item. We use it for updates.
            self.keys[table] = message['keys']
            if table == 'orderBookL2':
                return self.update_orderBookL2(action, message['data'])

            self.data[table] += message['data']
        elif action == 'insert':
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

        elif action == 'update':
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
        elif action == 'delete':
            self.logger.debug('%s: deleting %s' % (table, message['data']))
            if table == 'orderBookL2':
                return self.update_orderBookL2(action, message['data'])
            # Locate the item in the collection and remove it.
            for deleteData in message['data']:
                item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                self.data[table].remove(item)
        else:
            raise Exception("Unknown action: %s" % action)

    def update_orderBookL2(self, method, data):
        self.logger.debug(json.dumps(data))
        if method == 'partial':
            self.data['orderBookL2'] = data
        elif method == 'delete':
            for delete in data:
                level = next(level for level in
                    self.data['orderBookL2'] if level['id'] == delete['id'])
                if level:
                    self.data['orderBookL2'].remove(level)
        elif method == 'insert':
            for level in data:
                self.data['orderBookL2'].append(level)
        elif method == 'update':
            for update in data:
                level = next(level for level in self.data['orderBookL2']
                                       if level['id'] == update['id'])
                level['size'] = update['size']

    def __on_open(self, ws):
        self.logger.debug("Websocket Opened.")

    def __on_close(self, ws):
        self.logger.info('Websocket Closed')
        self.exit()

    def __on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.data = {}
        self.keys = {}
        self.exited = False
        self._error = None


def findItemByKeys(keys, table, matchData):
    for item in table:
        matched = True
        for key in keys:
            if item[key] != matchData[key]:
                matched = False
        if matched:
            return item

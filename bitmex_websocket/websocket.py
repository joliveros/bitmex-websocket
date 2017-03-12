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

        # Connected. Wait for partials
        # self.__wait_for_symbol(symbol)
        # if self.shouldAuth:
        #     self.__wait_for_account()
        # self.logger.info('Got all market data. Starting.')

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
        '''Connect to the websocket in a thread.'''

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


    def init_websocket(self):
        wsURL = self.build_websocket_url()
        self.logger.debug("Connecting to %s" % (wsURL))
        self.ws = websocket.WebSocketApp(
            wsURL,
            on_message=self.__on_message,
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
    # Data methods
    #

    def get_instrument(self, symbol):
        instruments = self.data['instrument']
        matchingInstruments = [i for i in instruments if i['symbol'] == symbol]
        if len(matchingInstruments) == 0:
            raise Exception("Unable to find instrument or index with symbol: " + symbol)
        instrument = matchingInstruments[0]
        # Turn the 'tickSize' into 'tickLog' for use in rounding
        # http://stackoverflow.com/a/6190291/832202
        instrument['tickLog'] = decimal.Decimal(str(instrument['tickSize'])).as_tuple().exponent * -1
        return instrument

    def get_ticker(self, symbol):
        '''Return a ticker object. Generated from instrument.'''

        instrument = self.get_instrument(symbol)

        # If this is an index, we have to get the data from the last trade.
        if instrument['symbol'][0] == '.':
            ticker = {}
            ticker['mid'] = ticker['buy'] = ticker['sell'] = ticker['last'] = instrument['markPrice']
        # Normal instrument
        else:
            bid = instrument['bidPrice'] or instrument['lastPrice']
            ask = instrument['askPrice'] or instrument['lastPrice']
            ticker = {
                "last": instrument['lastPrice'],
                "buy": bid,
                "sell": ask,
                "mid": (bid + ask) / 2
            }

        # The instrument has a tickSize. Use it to round values.
        return {k: round(float(v or 0), instrument['tickLog']) for k, v in iteritems(ticker)}

    def funds(self):
        return self.data['margin'][0]

    def market_depth(self, symbol):
        raise NotImplementedError('orderBook is not subscribed; use askPrice and bidPrice on instrument')
        # return self.data['orderBook25'][0]

    def open_orders(self, clOrdIDPrefix):
        orders = self.data['order']
        # Filter to only open orders (leavesQty > 0) and those that we actually placed
        return [o for o in orders if str(o['clOrdID']).startswith(clOrdIDPrefix) and o['leavesQty'] > 0]

    def position(self, symbol):
        positions = self.data['position']
        pos = [p for p in positions if p['symbol'] == symbol]
        if len(pos) == 0:
            # No position found; stub it
            return {'avgCostPrice': 0, 'avgEntryPrice': 0, 'currentQty': 0, 'symbol': symbol}
        return pos[0]

    def recent_trades(self):
        return self.data['trade']

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

        if not settings.API_KEY:
            self.logger.info("Authenticating with email/password.")
            return [
                "email: " + settings.LOGIN,
                "password: " + settings.PASSWORD
            ]
        else:
            self.logger.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature of a nonce and
            # the WS API endpoint.
            nonce = generate_nonce()
            return [
                "api-nonce: " + str(nonce),
                "api-signature: " + generate_signature(settings.API_SECRET, 'GET', '/realtime', nonce, ''),
                "api-key:" + settings.API_KEY
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

    def __on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        message = json.loads(message)
        self.logger.debug(json.dumps(message))

        table = message['table'] if 'table' in message else None
        action = message['action'] if 'action' in message else None
        try:
            if 'subscribe' in message:
                if message['success']:
                    self.logger.debug("Subscribed to %s." % message['subscribe'])
                else:
                    self.error("Unable to subscribe to %s. Error: \"%s\" Please check and restart." %
                               (message['request']['args'][0], message['error']))
            elif 'status' in message:
                if message['status'] == 400:
                    self.error(message['error'])
                if message['status'] == 401:
                    self.error("API Key incorrect, please check and restart.")
            elif action:

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
                    self.data[table] += message['data']
                    # Keys are communicated on partials to let you know how to uniquely identify
                    # an item. We use it for updates.
                    self.keys[table] = message['keys']
                elif action == 'insert':
                    self.logger.debug('%s: inserting %s' % (table, message['data']))
                    self.data[table] += message['data']

                    # Limit the max length of the table to avoid excessive memory usage.
                    # Don't trim orders because we'll lose valuable state if we do.
                    if table != 'order' and len(self.data[table]) > BitMEXWebsocket.MAX_TABLE_LEN:
                        self.data[table] = self.data[table][(BitMEXWebsocket.MAX_TABLE_LEN // 2):]

                elif action == 'update':
                    self.logger.debug('%s: updating %s' % (table, message['data']))
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
                    # Locate the item in the collection and remove it.
                    for deleteData in message['data']:
                        item = findItemByKeys(self.keys[table], self.data[table], deleteData)
                        self.data[table].remove(item)
                else:
                    raise Exception("Unknown action: %s" % action)
        except:
            self.logger.error(traceback.format_exc())

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

if __name__ == "__main__":
    # create console handler and set level to debug
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    ch = logging.StreamHandler()
    # create formatter
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    # add formatter to ch
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    ws = BitMEXWebsocket()
    ws.logger = logger
    ws.connect("https://testnet.bitmex.com/api/v1")
    while(ws.ws.sock.connected):
        sleep(1)

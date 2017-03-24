from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
import sys
import websocket
import threading
import traceback
from time import sleep
import json
from bitmex_websocket.settings import settings
from bitmex_websocket.utils.log import setup_custom_logger
from bitmex_websocket.auth.APIKeyAuth import generate_nonce, generate_signature
from urllib.parse import urlparse
from pyee import EventEmitter

PING_MESSAGE_PREFIX = 'primus::ping::'

class BitMEXWebsocket(EventEmitter):
    def __init__(self):
        EventEmitter.__init__(self)
        self.logger = setup_custom_logger('BitMEXWebsocket')
        self.channels = []
        self.__reset()

    def connect(
            self,
            shouldAuth=False,
            websocket=None,
            heartbeatEnabled=False):
        '''Connect to the websocket and initialize data stores.'''

        self.logger.debug("Connecting WebSocket.")
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

    def subscribe(self, action, channel, instrument, action_handler):
        channelKey = "{}:{}".format(channel, instrument)
        subscriptionMsg = {"op": "subscribe", "args": [channelKey]}
        action_event_key = self.gen_action_event_key(action,
                                                     instrument,
                                                     channel)
        self.logger.debug("Subscribe to %s" % (action_event_key))
        self.on(action_event_key, action_handler)

        if channelKey not in self.channels:
            self.channels.append(channelKey)
            self.logger.debug(self.channels)
            self.logger.info(subscriptionMsg)
            self.send_message(subscriptionMsg)

    def send_message(self, message):
        self.ws.send(json.dumps(message))

    def error(self, err):
        self._error = err
        self.logger.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()

    def is_connected(self):
        self.ws.sock.connected

    def on_subscribe(self, message):
        if message['success']:
            self.logger.debug("Subscribed to %s." % message['subscribe'])
            if message['subscribe'] not in self.channels:
                self.channels.append(message['subscribe'])
        else:
            self.error("Unable to subscribe to %s. Error: \"%s\" Please\
            check and restart." % (
                message['request']['args'][0], message['error']))

    def on_message(self, ws, message):
        '''Handler for parsing WS messages.'''
        # Check if ping message
        ping_message = message[:14]
        if ping_message == PING_MESSAGE_PREFIX:
            return self.emit('ping', message)

        self.logger.debug(json.dumps(message, indent=4, sort_keys=True))
        message = json.loads(message)

        action = message['action'] if 'action' in message else None

        try:
            if action:
                instrument = message['data'][0]['symbol']
                table = message['table']
                action_event = self.gen_action_event_key(action,
                                                         instrument,
                                                         table)
                self.logger.debug(action_event)
                self.emit(action_event, message)
            elif 'subscribe' in message:
                self.emit('subscribe', message)
            elif 'error' in message:
                self.error(message['error'])
            elif 'status' in message:
                self.emit('status', message)

        except:
            self.logger.error(traceback.format_exc())

    def on_status(self, message):
        if message['status'] == 400:
            self.error(message['error'])
        if message['status'] == 401:
            self.error("API Key incorrect, please check and restart.")

    def gen_action_event_key(self, event, instrument, table):
        return "%s:%s:%s" % (event, instrument, table)

    #
    # Private methods
    #
    def __get_auth(self):
        '''Return auth headers. Will use API Keys if present in settings.'''
        self.logger.debug(self.shouldAuth)
        if self.shouldAuth:
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
        else:
            return []

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

    def __on_open(self, ws):
        self.logger.debug("Websocket Opened.")

    def __on_close(self, ws):
        self.logger.info('Websocket Closed')
        self.exit()

    def __on_error(self, ws, error):
        if not self.exited:
            self.error(error)

    def __reset(self):
        self.remove_all_listeners()
        self.on('subscribe', self.on_subscribe)
        self.exited = False
        self._error = None

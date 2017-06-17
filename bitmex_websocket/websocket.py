from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from builtins import *
from bitmex_websocket import constants
from bitmex_websocket.auth.APIKeyAuth import generate_nonce, generate_signature
from bitmex_websocket.settings import settings
from pyee import EventEmitter
from time import sleep
from urllib.parse import urlparse
import json
import sys
import threading
import time
import traceback
import websocket
import alog

PING_MESSAGE_PREFIX = 'primus::ping::'
CONN_TIMEOUT = 60

__all__ = ['BitMEXWebsocket']


class BitMEXWebsocket(EventEmitter):
    def __init__(self):
        EventEmitter.__init__(self)
        self.channels = []
        self.__reset()

    def connect(
            self,
            shouldAuth=False,
            websocket=None,
            heartbeatEnabled=True):
        '''Connect to the websocket and initialize data stores.'''

        alog.debug("Connecting WebSocket.")
        self.shouldAuth = shouldAuth
        alog.debug(f'heartbeatEnabled: {heartbeatEnabled}')
        self.heartbeatEnabled = heartbeatEnabled
        self.connect_websocket()

        alog.info('Connected to WS. Waiting for data images, this may \
        take a moment...')

    def re_connect(self):
        sleep(1)
        self.connect_websocket()

        for channel in self.channels:
            self._subscribe_to_channel(channel)

    def build_websocket_url(self, base_url=settings.BASE_URL):
        alog.debug('Build websocket url from: %s' % (base_url))

        urlParts = list(urlparse(base_url))
        queryString = ''
        if self.heartbeatEnabled:
            queryString = '?heartbeat=true'

        url = "wss://{}/realtime{}".format(urlParts[1], queryString)
        alog.debug(url)
        return url

    def connect_websocket(self):
        """Connect to the websocket in a thread."""
        alog.debug("### Connecting Websocket ###")

        self.init_websocket()

        # setup websocket.run_forever arguments
        wsRunArgs = {}
        if self.heartbeatEnabled:
            wsRunArgs['ping_timeout'] = 20
            wsRunArgs['ping_interval'] = 60

        alog.debug("websocket.run_forever: %s" % (wsRunArgs))

        # Run the websocket on another thread and enable heartbeat
        self.wst = threading.Thread(
            target=lambda: self.websocket_run_forever(wsRunArgs)
        )
        self.wst.daemon = True
        self.wst.start()
        alog.info("Started thread")
        self.wait_for_connection()

    def wait_for_connection(self):
        conn_timeout = CONN_TIMEOUT
        # Wait for connect before continuing
        while (not self.ws.sock or not self.ws.sock.connected) \
                and conn_timeout and not self._error:
            sleep(1)
            conn_timeout -= 1

        if not conn_timeout or self._error:
            alog.error("Couldn't connect to WS! Exiting.")
            self.exit()
            sys.exit(1)

    def init_websocket(self):
        wsURL = self.build_websocket_url()
        alog.debug("Connecting to %s" % (wsURL))
        self.ws = websocket.WebSocketApp(wsURL,
                                         on_message=self.__on_message,
                                         on_close=self.__on_close,
                                         on_open=self.__on_open,
                                         on_error=self.__on_error,
                                         header=self.__get_auth(),
                                         on_ping=self.__on_ping,
                                         on_pong=self.__on_pong)

    def websocket_run_forever(self, args):
        self.ws.run_forever(**args)

    def __on_ping(self, frame, data):
        alog.debug('## ping')
        alog.debug(data)

    def __on_pong(self, frame, data):
        alog.debug('## pong')
        alog.debug(data)

    def subscribe_action(self, action, channel, instrument, action_handler):
        channelKey = "{}:{}".format(channel, instrument)
        alog.debug("Subscribe to action: %s" % (channelKey))
        subscriptionMsg = {"op": "subscribe", "args": [channelKey]}
        action_event_key = self.gen_action_event_key(action,
                                                     instrument,
                                                     channel)
        alog.debug("Subscribe to %s" % (action_event_key))
        self.on(action_event_key, action_handler)

        if channelKey not in self.channels:
            self.channels.append(channelKey)
            alog.debug(subscriptionMsg)
            self.send_message(subscriptionMsg)

    def subscribe(self, channel, handler):
        self._subscribe_to_channel(channel)
        self.on(channel, handler)
        if channel not in self.channels:
            self.channels.append(channel)

    def _subscribe_to_channel(self, channel):
        subscriptionMsg = {"op": "subscribe", "args": [channel]}
        self.send_message(subscriptionMsg)

    def send_message(self, message):
        self.ws.send(json.dumps(message))

    def error(self, err):
        alog.debug('this error...')
        self._error = err
        alog.error(err)
        self.exit()

    def exit(self):
        self.exited = True
        self.ws.close()

    def is_connected(self):
        self.ws.sock.connected

    def on_subscribe(self, message):
        if message['success']:
            alog.debug("Subscribed to %s." % message['subscribe'])
        else:
            self.error("Unable to subscribe to %s. Error: \"%s\" Please\
            check and restart." % (
                message['request']['args'][0], message['error']))

    def on_ping(self, message):
        timestamp = float(time.time() * 1000)
        ping_timestamp = float(message[14:])
        latency = timestamp - ping_timestamp
        alog.debug("ping: %s" % (message))
        alog.debug("ping timestamp: %s" % (timestamp))
        alog.debug("message latency: %s" % (latency))
        self.emit('latency', latency)
        alog.debug(int(timestamp))
        self.send_message("primus::pong::%s" % (timestamp))

    def __on_message(self, ws, message):
        self.on_message(message)

    def on_message(self, message):
        '''Handler for parsing WS messages.'''
        # Check if ping message
        ping_message = message[:14]
        alog.debug(ping_message)
        if ping_message == PING_MESSAGE_PREFIX:
            alog.debug(message)
            return self.emit('ping', message)

        message = json.loads(message)
        alog.debug(json.dumps(message, indent=4, sort_keys=True))

        action = message['action'] if 'action' in message else None

        try:
            if action:
                table = message['table']
                event_name = ''
                if table in constants.CHANNELS:
                    event_name = "%s:%s" % (action, table)
                else:
                    if len(message['data']) > 0:
                        instrument = message['data'][0]['symbol']
                        event_name = self.gen_action_event_key(action,
                                                               instrument,
                                                               table)
                alog.debug(event_name)
                self.emit(event_name, message)
            elif 'subscribe' in message:
                self.emit('subscribe', message)
            elif 'error' in message:
                self.error(message['error'])
            elif 'status' in message:
                self.emit('status', message)

        except:
            alog.error(traceback.format_exc())

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
        alog.debug('shouldAuth: %s' % self.shouldAuth)
        if self.shouldAuth:
            alog.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature
            # of a nonce and the WS API endpoint.
            alog.debug(settings.BITMEX_API_KEY)
            nonce = generate_nonce()
            api_signature = generate_signature(
                settings.BITMEX_API_SECRET, 'GET', '/realtime', nonce, '')

            auth = [
                "api-nonce: " + str(nonce),
                "api-signature: " + api_signature,
                "api-key:" + settings.BITMEX_API_KEY
            ]
            alog.debug(auth)

            return auth
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
        alog.debug("Websocket Opened.")

    def __on_close(self, ws):
        alog.info('Websocket Closed')
        self.emit('close')
        self.exit()
        self.re_connect()

    def __on_error(self, ws, error):
        if not self.exited:
            self.emit('error', error)
            self.error(error)
            self.exit()
            self.re_connect()

    def __reset(self):
        self.remove_all_listeners()
        self.on('subscribe', self.on_subscribe)
        self.on('ping', self.on_ping)
        self.exited = False
        self._error = None

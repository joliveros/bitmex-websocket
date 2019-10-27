from bitmex_websocket.auth.api_key_auth import generate_nonce,\
    generate_signature
from bitmex_websocket.settings import settings
from pyee import EventEmitter
from urllib.parse import urlparse
from websocket import WebSocketApp

import alog
import json
import ssl
import time

__all__ = ['BitMEXWebsocket']


class BitMEXWebsocketConnectionError(Exception):
    pass


class BitMEXWebsocket(
    WebSocketApp,
    EventEmitter
):
    def __init__(
        self,
        should_auth=False,
        heartbeat=True,
        ping_interval=10,
        ping_timeout=9,
        **kwargs
    ):
        self.ping_timeout = ping_timeout
        self.ping_interval = ping_interval
        self.should_auth = should_auth
        self.heartbeat = heartbeat
        self.channels = []
        self.reconnect_count = 0

        super().__init__(
            url=self.gen_url(),
            header=self.header(),
            on_message=self.on_message,
            on_close=self.on_close,
            on_open=self.on_open,
            on_error=self.on_error,
            on_pong=self.on_pong,
            **kwargs
        )
        super(EventEmitter, self).__init__()

        self.on('subscribe', self.on_subscribe)

    def gen_url(self):
        base_url = settings.BASE_URL
        url_parts = list(urlparse(base_url))
        query_string = ''

        if self.heartbeat:
            query_string = '?heartbeat=true'

        url = "wss://{}/realtime{}".format(url_parts[1], query_string)

        return url

    def run_forever(self, **kwargs):
        """Connect to the websocket in a thread."""

        # setup websocket.run_forever arguments
        ws_run_args = {
            'sslopt': {"cert_reqs": ssl.CERT_NONE}
        }

        if self.heartbeat:
            ws_run_args['ping_timeout'] = self.ping_timeout
            ws_run_args['ping_interval'] = self.ping_interval

        alog.debug(ws_run_args)

        super().run_forever(**ws_run_args)

    def on_pong(self, message):
        timestamp = float(time.time() * 1000)
        latency = timestamp - (self.last_ping_tm * 1000)
        self.emit('latency', latency)

    def subscribe(self, channel: str):
        subscription_msg = {"op": "subscribe", "args": [channel]}
        self._send_message(subscription_msg)

    def _send_message(self, message):
        self.send(json.dumps(message))

    def is_connected(self):
        return self.sock.connected

    @staticmethod
    def on_subscribe(message):
        if message['success']:
            alog.debug("Subscribed to %s." % message['subscribe'])
        else:
            raise Exception('Unable to subsribe.')

    def on_message(self, message):
        """Handler for parsing WS messages."""
        message = json.loads(message)

        if 'error' in message:
            self.on_error(message['error'])

        action = message['action'] if 'action' in message else None

        if action:
            self.emit('action', message)

        elif 'subscribe' in message:
            self.emit('subscribe', message)

        elif 'status' in message:
            self.emit('status', message)

    def header(self):
        """Return auth headers. Will use API Keys if present in settings."""
        auth_header = []

        if self.should_auth:
            alog.info("Authenticating with API Key.")
            # To auth to the WS using an API key, we generate a signature
            # of a nonce and the WS API endpoint.
            alog.debug(settings.BITMEX_API_KEY)
            nonce = generate_nonce()
            api_signature = generate_signature(
                settings.BITMEX_API_SECRET, 'GET', '/realtime', nonce, '')

            auth_header = [
                "api-nonce: " + str(nonce),
                "api-signature: " + api_signature,
                "api-key:" + settings.BITMEX_API_KEY
            ]

        return auth_header

    def on_open(self):
        alog.debug("Websocket Opened.")
        self.emit('open')

    def on_close(self):
        alog.info('Websocket Closed')

    def on_error(self, error):
        raise BitMEXWebsocketConnectionError(error)


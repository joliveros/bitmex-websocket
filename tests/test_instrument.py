import alog
import pytest
from mock import PropertyMock, MagicMock, mock

from bitmex_websocket import Instrument
from bitmex_websocket._instrument import SubscribeToAtLeastOneChannelException, \
    SubscribeToSecureChannelException
from bitmex_websocket.constants import Channels, SecureChannels, \
    SecureInstrumentChannels
from tests.helpers import message_fixtures

fixtures = message_fixtures()
orderBookL2_data = fixtures['orderBookL2']
instrument_data = fixtures['instrument']


class TestInstrument(object):
    def test_raises_exception_no_channel_subscribed(self):
        with pytest.raises(SubscribeToAtLeastOneChannelException):
            Instrument()

    def test_only_public_channels(self):
        instrument = Instrument(channels=[Channels.connected])

        assert [Channels.connected] == instrument.channels

    def test_public_and_secure_channels_are_in_channels_list(self, mocker):
        header_mock = mocker.patch(
            'bitmex_websocket._bitmex_websocket.BitMEXWebsocket.header')
        header_mock.return_value = []

        channels = [
            Channels.connected, SecureChannels.margin]
        instrument = Instrument(should_auth=True, channels=channels)

        assert channels == instrument.channels

    def test_raises_exception_if_secure_channels_are_specified_without_auth(
            self):
        with pytest.raises(SubscribeToSecureChannelException):
            channels = [
                Channels.connected, SecureChannels.margin]

            instrument = Instrument(channels=channels)

            assert channels == instrument.channels

    def test_does_not_raise_exception_when_subscribing_secure_channel(
            self,
            mocker):
        header_mock = mocker.patch(
            'bitmex_websocket._bitmex_websocket.BitMEXWebsocket.header')
        header_mock.return_value = []

        channels = [
            Channels.connected, SecureChannels.margin]

        instrument = Instrument(channels=channels, should_auth=True)
        instrument.emit('open')

        assert channels == instrument.channels

    def test_subscribe_to_public_channels(self, mocker):
        header_mock = mocker.patch(
            'bitmex_websocket._bitmex_websocket.BitMEXWebsocket.header')
        header_mock.return_value = []

        subscribe_mock: MagicMock = mocker.patch(
            'bitmex_websocket._bitmex_websocket.BitMEXWebsocket.subscribe')

        channels = [
            Channels.connected,
            SecureChannels.margin,
            SecureInstrumentChannels.order
        ]

        instrument = Instrument(channels=channels, should_auth=True)

        instrument.subscribe_channels()

        assert channels == instrument.channels

        subscribe_mock.assert_has_calls([mock.call('margin:XBTUSD'),
                                         mock.call('order:XBTUSD')])



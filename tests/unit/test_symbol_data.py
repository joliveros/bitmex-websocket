from __future__ import (
    absolute_import,
    division,
    print_function,
    unicode_literals
)
from builtins import *
from bitmex_websocket.symbol_data import SymbolData
from tests import *
from tests.helpers import *
import pytest


def test_on_init_connects_websocket(mocker):
    connect_websocket = mocker.patch(
        'bitmex_websocket.symbol_data.SymbolData.connect_websocket')

    SymbolData()
    connect_websocket.assert_called_once()

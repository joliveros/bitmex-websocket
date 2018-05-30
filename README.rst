bitmex-websocket
================
.. image:: https://api.travis-ci.org/joliveros/bitmex-websocket.svg?branch=master
    :target: https://travis-ci.org/joliveros/bitmex-websocket
.. image:: https://requires.io/github/joliveros/bitmex-websocket/requirements.svg?branch=master
    :target: https://requires.io/github/joliveros/bitmex-websocket/requirements?branch=master
.. image:: https://coveralls.io/repos/joliveros/bitmex-websocket/badge.svg?branch=master
    :target: https://coveralls.io/r/joliveros/bitmex-websocket?branch=master

Install
-------

.. code-block:: sh

    $ pip install bitmex-websocket

Usage
-----

1. First you should set your `BITMEX_API_KEY` and `BITMEX_API_SECRET`. It can
   be done as follows:

.. code-block:: sh

    $ cp .env.example .env
    #  edit .env to reflect your API key and secret
    $ source .env

2. Then in your project you can consume `Instrument` as follows:

.. code-block:: python

    import websocket

    from bitmex_websocket import Instrument
    from bitmex_websocket.constants import InstrumentChannels

    websocket.enableTrace(True)


    channels = [
        InstrumentChannels.quote,
        InstrumentChannels.trade,
        InstrumentChannels.orderBookL2
    ]

    XBTUSD = Instrument(symbol='XBTUSD',
                        channels=channels)
    XBTUSD.on('action', lambda msg: print(message))

    XBTUSD.run_forever()

Examples
--------

Run example scripts:

.. code-block:: sh

    $ RUN_ENV=development python -m ./examples/example-2.py

Tests
-----

Testing is set up using `pytest <http://pytest.org>` and coverage is handled
with the pytest-cov plugin.

Run your tests with `pytest` in the root directory.

Coverage is ran by default and is set in the `pytest.ini` file.
To see an html output of coverage open `htmlcov/index.html` after running the tests.

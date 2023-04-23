bitmex-websocket
================

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
    XBTUSD.on('action', lambda msg: print(msg))

    XBTUSD.run_forever()

TestNet
--------

You may change the `BASE_URL` by setting the `BITMEX_BASE_URL` environment variable to:
`https://testnet.bitmex.com/api/v1/`.



Examples
--------

Run example scripts:

.. code-block:: sh

    $ ./examples/example.py


Output:

.. code-block:: sh
    2023-04-22 18:11:02 INFO  [examples.example:23] 
    [{'askPrice': 27778.0,
      'askSize': 68200,
      'bidPrice': 27777.5,
      'bidSize': 11400,
      'symbol': 'XBTUSD',
      'timestamp': '2023-04-23T00:11:02.184Z'}]
    ++Rcv raw: b'\x81~\x00\xad{"table":"quote","action":"insert","data":[{"timestamp":"2023-04-23T00:11:02.192Z","symbol":"XBTUSD","bidSize":11400,"bidPrice":27777.5,"askPrice":27778.0,"askSize":74700}]}'
    ++Rcv decoded: fin=1 opcode=1 data=b'{"table":"quote","action":"insert","data":[{"timestamp":"2023-04-23T00:11:02.192Z","symbol":"XBTUSD","bidSize":11400,"bidPrice":27777.5,"askPrice":27778.0,"askSize":74700}]}'
    2023-04-22 18:11:02 INFO  [examples.example:23] 
    [{'askPrice': 27778.0,
      'askSize': 74700,
      'bidPrice': 27777.5,
      'bidSize': 11400,
      'symbol': 'XBTUSD',
      'timestamp': '2023-04-23T00:11:02.192Z'}]


Tests
-----

Testing is set up using `pytest <http://pytest.org>` and coverage is handled
with the pytest-cov plugin.

Run your tests with `pytest` in the root directory.

Coverage is ran by default and is set in the `pytest.ini` file.
To see an html output of coverage open `htmlcov/index.html` after running the tests.

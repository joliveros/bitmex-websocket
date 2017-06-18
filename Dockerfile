FROM codequants/bitmex-websocket:base

ENV MODULE_NAME bitmex-websocket
ARG SECRETS_PASS

COPY . /src

WORKDIR /src

RUN pip install -r requirements.txt -r requirements-test.txt

RUN pytest

RUN python ./setup.py install

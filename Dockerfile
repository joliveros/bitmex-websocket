FROM codequants/bitmex-websocket:base

ENV MODULE_NAME bitmex-websocket

COPY . /src

WORKDIR /src


RUN pip install --upgrade pip setuptools && \
    pip install -r requirements.txt -r requirements-test.txt

#RUN pytest

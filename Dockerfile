FROM python:3.6.1-slim

COPY . /src

WORKDIR /src

RUN pip install -r requirements.txt -r requirements-test.txt

RUN pytest

RUN python ./setup.py install

FROM python:3.10.4-slim

# Install zmq
RUN pip install pyzmq requests

# Dirpath to service source
ARG MAIN_PATH
ARG COMMON_PATH

# Copy sources
COPY ${MAIN_PATH} /main.py
COPY ${COMMON_PATH} /common

ENTRYPOINT ["python3", "main.py"]

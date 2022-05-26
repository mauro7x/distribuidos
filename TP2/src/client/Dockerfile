FROM python:3.10.4-slim

# Install zmq
RUN pip install pyzmq

# Dirpath to service source
ARG DIR_PATH
ARG COMMON_PATH

# Copy sources
COPY ${DIR_PATH} /
COPY ${COMMON_PATH} /common

ENTRYPOINT ["python3", "main.py"]

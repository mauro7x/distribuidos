FROM python:3.10.4-slim

# Install zmq
RUN pip install pyzmq

# Dirpath to service source
ARG MAIN_PATH

# Copy sources
COPY ${MAIN_PATH} /main.py
COPY common /common

CMD ["python3", "main.py"]

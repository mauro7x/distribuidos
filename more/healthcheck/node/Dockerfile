FROM python:3.10.4-slim

# Install zmq
RUN pip install pyzmq

COPY . .

ENTRYPOINT ["python3", "main.py"]

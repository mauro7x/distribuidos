FROM python:3.10.4-slim

# Install dependencies
RUN pip install pyzmq docker

COPY monitor/ /
COPY common/ /common

ENTRYPOINT ["python3", "main.py"]

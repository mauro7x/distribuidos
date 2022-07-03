FROM python:3.10.4-slim

# Install dependencies
RUN pip install pyzmq
RUN pip install docker

COPY . .

ENTRYPOINT ["python3", "main.py"]

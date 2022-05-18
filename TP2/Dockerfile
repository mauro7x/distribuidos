FROM python:3.10.4-slim

# Dirpath to service source
ARG SRC_PATH
ARG COMMON_PATH

# Copy sources
COPY ${SRC_PATH}/main.py /
COPY ${COMMON_PATH} /common

CMD ["python3", "main.py"]

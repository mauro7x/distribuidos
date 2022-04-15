#!/bin/bash

# Server configuration
HOST="${HOST:-server}"
PORT="${PORT:-12345}"

# Test case
MSG="Hello World"
EXPECTED="Hello World"

# Run netcat test
OUTPUT=$(echo $MSG | nc $HOST $PORT)
if [ "$OUTPUT" == "$EXPECTED" ]; then
  echo "Success!"
  exit 0
else
  echo "Test failed:"
  echo "  + Expected: $EXPECTED"
  echo "  - Received: $OUTPUT"
  exit 1
fi

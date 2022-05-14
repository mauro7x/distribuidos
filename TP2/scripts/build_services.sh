#!/bin/bash

# Exit when any command fails
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Special chars
CHECK="${GREEN}\xE2\x9C\x93${NC}"

# Config
VERBOSE="${VERBOSE:-false}"

# Functions

# $1 = name
function build {
    echo -n -e "> Building ${CYAN}$1${NC}... "
    CMD="docker build -t tp2_${1}:latest -f ./docker/Dockerfile ./services/${1}"
    
    set +e
    if ${VERBOSE}; then
        OUTPUT=$(DOCKER_BUILDKIT=1 ${CMD})
    else
        OUTPUT=$(DOCKER_BUILDKIT=1 ${CMD} 2>&1)
    fi
    RESULT=$?
    set -e

    if [ $RESULT -eq 0 ]; then
        echo -e "${CHECK}"
    else
        echo -e "${RED}failed. See output:${NC}\n"
        echo -e "$OUTPUT"
        exit 1
    fi
}

# Main execution

failed=false
for SERVICE_DIRPATH in ./services/*; do
    SERVICE="$(basename ${SERVICE_DIRPATH})"
    build "${SERVICE}"
done

echo -e "\n${GREEN}Success!${NC}"

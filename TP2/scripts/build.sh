#!/bin/bash

# Exit when any command fails
set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
CYAN='\033[0;36m'
CYANB='\033[1;36m'
NC='\033[0m'

# Special chars
CHECK="${GREEN}\xE2\x9C\x93${NC}"

# Config
VERBOSE="${VERBOSE:-false}"

# Functions

# $1 = name
# $2 = filepath
function build {
    echo -n -e "> Building ${CYAN}$1${NC}... "
    CMD="docker build \
        -t tp2_${1}:latest \
        -f ./Dockerfile \
        --build-arg MAIN_PATH=${2} \
        --build-arg COMMON_PATH=src/common \
        ."
    
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

# $1 = list of filepaths
function build_filepaths {
    for filepath in $@; do
        name="$(basename ${filepath} .py)"
        build "${name}" "${filepath}"
    done
}

# Main execution

services=$(ls ./src/*.py)
filters=$(ls ./src/filters/*.py)

echo -e "${CYANB}Services:${NC}"
build_filepaths $services

echo -e "\n${CYANB}Filters:${NC}"
build_filepaths $filters

echo -e "\n${GREEN}Success!${NC}"

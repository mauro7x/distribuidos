#!/bin/bash

# Exit when any command fails
set -e

# Config
VERBOSE="${VERBOSE:-false}"
PRETTY="${PRETTY:-true}"

# Colors and especial formatting

if ${PRETTY}; then
    GREEN='\033[0;32m'
    RED='\033[0;31m'
    CYAN='\033[0;36m'
    CYANB='\033[1;36m'
    NC='\033[0m'
    CHECK="${GREEN}\xE2\x9C\x93${NC}"
else
    GREEN=''
    RED=''
    CYAN=''
    CYANB=''
    NC=''
    CHECK='done.'
fi

# Functions

# $1 = cmd
function run_cmd {
    set +e
    if ${VERBOSE}; then
        OUTPUT=$(DOCKER_BUILDKIT=1 ${1})
    else
        OUTPUT=$(DOCKER_BUILDKIT=1 ${1} 2>&1)
    fi
    RESULT=$?
    set -e

    if [ $RESULT -eq 0 ]; then
        echo -e "${CHECK}"
    else
        echo -e "${RED}failed. See output:${NC}\n"
        echo -e "${OUTPUT}"
        exit 1
    fi
}

# $1 = name
function build_service {
    echo -n -e "> Building ${CYAN}$1${NC} service... "
    run_cmd "docker build -f ./.services/${1}/Dockerfile -t ${1}:latest ."
}


# Main execution

# 1. Generate services
echo "(1/3) - Setup workspace"
cd ./scripts
echo -n -e "> Scaling pipeline... "
run_cmd "python3 scale_pipeline.py"
echo -n -e "> Generating Docker Compose file... "
run_cmd "python3 generate_docker_compose.py"
echo -n -e "> Generating services... "
run_cmd "python3 generate_services.py"
cd ../

# 2. Build services
echo -e "\n(2/3) - Build images"
echo -n -e "> Building ${CYAN}base image${NC}... "
run_cmd "docker build -f ./base/images/python-base.dockerfile -t rabbitmq-python-base:0.0.1 ."
echo -n -e "> Building ${CYAN}rabbitmq${NC}... "
run_cmd "docker build -f ./rabbitmq/Dockerfile -t rabbitmq:latest ."
echo -n -e "> Building ${CYAN}client${NC}... "
run_cmd "docker build -f ./entities/client/Dockerfile -t client:latest ."
echo -n -e "> Building ${CYAN}monitor${NC}... "
run_cmd "docker build -f ./monitor/Dockerfile -t monitor:latest ."
services=$(ls ./.services)
for service in $services; do
    build_service "${service}"
done

# 3. Clean workspace
echo -e "\n(3/3) - Clean workspace"
echo -n -e "> Removing services... "
run_cmd "rm -rf .services"

echo -e "\n${GREEN}Success!${NC}"

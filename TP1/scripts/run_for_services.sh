#!/bin/bash

# Exit when any command fails
set -e

# Vars
CMD="$@"
SERVICES_DIRPATH="${SERVICES_DIRPATH:-./services}"
VERBOSE="${VERBOSE:-false}"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
GREY='\033[1;30m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
CYANB='\033[1;36m'
NC='\033[0m'

# Special chars
CHECK="${GREEN}\xE2\x9C\x93${NC}"

# Functions

function run {
    set +e
    OUTPUT=$($@ 2>&1)
    RESULT=$?
    set -e

    if [ ${RESULT} -eq 0 ]; then
        echo -e " ${CHECK}"
        return 0
    fi

    echo -e " ${RED}X${NC}"
    if ${VERBOSE}; then
        echo -e "${GREY}(VERBOSE)${NC} Output:\n${OUTPUT}\n"
    fi

    exit ${RESULT}
}

# Main execution

if [ "${CMD}" == "" ]; then
    echo -e "${YELLOW}Warning: empty command received!${NC}"
    exit 1
fi

echo -e "Command received: ${CYAN}${CMD}${NC}\n"

cd ${SERVICES_DIRPATH}
failed=false
for SERVICE_DIRPATH in ./*; do
    SERVICE="$(basename ${SERVICE_DIRPATH})"
    echo -n -e "> Running on ${CYANB}${SERVICE}${NC}..."
    cd ${SERVICE}
    run "${CMD}"
    cd ..
done

echo -e "\n${GREEN}Success!${NC}"

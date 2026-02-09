#!/bin/bash
# wait-for-it.sh - Script para aguardar serviços estarem disponíveis

# Configurações
WAIT_FOR_IT_TIMEOUT=${WAIT_FOR_IT_TIMEOUT:-15}
WAIT_FOR_IT_STRICT=${WAIT_FOR_IT_STRICT:-1}
WAIT_FOR_IT_QUIET=${WAIT_FOR_IT_QUIET:-0}

# Função para checar disponibilidade do serviço
wait_for() {
    local hostport=$1
    local timeout=$2
    
    if [ "$WAIT_FOR_IT_QUIET" -eq 1 ]; then
        QUIET="--quiet"
    fi
    
    eval "set -- $hostport"
    local cmd="$1"
    shift
    local args="$@"
    
    echo "Waiting for $cmd $args to be ready..."
    
    # Para PostgreSQL
    if command -v nc >/dev/null 2>&1; then
        nc -z $cmd $args
        return $?
    elif command -v ncat >/dev/null 2>&1; then
        ncat -z $cmd $args
        return $?
    elif command -v wget >/dev/null 2>&1; then
        wget --quiet --tries=1 --spider --timeout=3 $cmd:$args >/dev/null 2>&1
        return $?
    elif command -v curl >/dev/null 2>&1; then
        curl --output /dev/null --silent --head --fail $cmd:$args >/dev/null 2>&1
        return $?
    else
        echo "Error: No network checking tool available"
        return 1
    fi
}

# Função principal
wait_for_service() {
    local hostport=$1
    local timeout=${2:-$WAIT_FOR_IT_TIMEOUT}
    
    for i in $(seq 1 $timeout); do
        if wait_for $hostport; then
            echo "Service is ready!"
            return 0
        fi
        echo "Waiting... ($i/$timeout)"
        sleep 1
    done
    
    echo "Timeout waiting for service $hostport"
    return 1
}

# Executar função principal se script for chamado diretamente
if [ "$WAIT_FOR_IT_QUIET" -eq 1 ]; then
    wait_for_service "$@" > /dev/null 2>&1
else
    wait_for_service "$@"
fi
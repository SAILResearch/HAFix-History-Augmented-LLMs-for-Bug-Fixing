#!/bin/bash

containers=(
    "codellama_7b_label"
    "codellama_7b_mask"
    "deepseek_coder_6.7b_label"
    "deepseek_coder_6.7b_mask"
    "deepseek_coder_v2_16b_label"
    "deepseek_coder_v2_16b_mask"
)

echo

while true; do
    clear
    echo "============= Ollama Status for All Containers ============="
    echo "============= $(date) ============="
    echo "Press Ctrl+C to stop"
    echo

    for container in "${containers[@]}"; do
        echo "--------------- $container ---------------"
        docker exec "$container" ollama ps 2>/dev/null || echo "Container not running or error"
        echo
    done

    echo "Press Ctrl+C to stop watching..."
    sleep 10
done
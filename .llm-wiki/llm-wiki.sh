#!/bin/bash
# llm-wiki wrapper — dispatches to the Python CLI tool
# Install: ln -s /mnt/d/Obsidian/Hub/WikiVault/.llm-wiki/llm-wiki.sh /usr/local/bin/llm-wiki

VAULT="${OBSIDIAN_VAULT_PATH:-/mnt/d/Obsidian/Hub/WikiVault}"
SCRIPT="$VAULT/.llm-wiki/llm-wiki.py"

if [ ! -f "$SCRIPT" ]; then
    echo "Error: llm-wiki.py not found at $SCRIPT"
    exit 1
fi

# Use Hermes venv python, or system python
PYTHON="$HOME/.hermes/hermes-agent/venv/bin/python3"
if [ ! -f "$PYTHON" ]; then
    PYTHON="python3"
fi

exec "$PYTHON" "$SCRIPT" "$@"

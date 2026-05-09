#!/bin/bash
export OBSIDIAN_VAULT_PATH="/mnt/d/Obsidian/Hub/WikiVault"
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh hot update
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh sync
exit 0

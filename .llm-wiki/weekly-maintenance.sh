#!/bin/bash
export OBSIDIAN_VAULT_PATH="/mnt/d/Obsidian/Hub/WikiVault"
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh hot report
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh decay --auto
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh graph
$OBSIDIAN_VAULT_PATH/.llm-wiki/llm-wiki.sh index
exit 0

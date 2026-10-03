#!/bin/bash
# Pre-commit hook: harvest proof metrics and update .ledger/index.jsonl
#
# This script is called by the pre-commit hook system. It:
# 1. Computes git write-tree hash (content identity of staged state)
# 2. Harvests all .ledger/**/*.json and .ledger/*.json sidecars
# 3. Reads previous ledger entry (if exists)
# 4. For each sidecar, compares hash.full against previous entry:
#    - If hash.full changed or proof is new: use sidecar data (proof was re-run)
#    - If hash.full matches previous entry: carry forward unchanged (carry-forward)
# 5. Computes suite.new/removed/changed deltas
# 6. Appends one JSON line to .ledger/index.jsonl
# 7. Stages .ledger/index.jsonl with git add

set -euo pipefail

# Find project root
PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)

# Exit silently if no ledger directory exists yet (no proofs run)
if [[ ! -d "$PROJECT_ROOT/.ledger" ]]; then
    exit 0
fi

# Compute git write-tree hash — content identity of staged state
TREE=$(git write-tree)

# Read parent tree and previous proof entries (if index.jsonl exists)
PARENT_TREE=""
PREVIOUS_PROOFS="{}"

if [[ -f "$PROJECT_ROOT/.ledger/index.jsonl" ]]; then
    # Get last line of index.jsonl
    LAST_LINE=$(tail -1 "$PROJECT_ROOT/.ledger/index.jsonl")
    PARENT_TREE=$(echo "$LAST_LINE" | jq -r '.tree // ""' 2>/dev/null || echo "")
    PREVIOUS_PROOFS=$(echo "$LAST_LINE" | jq -r '.proofs // {}' 2>/dev/null || echo "{}")
fi

# Get current branch
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")

# Get parent commit (the commit we're about to create will be on top of HEAD)
CURRENT_COMMIT=$(git rev-parse HEAD 2>/dev/null || echo "")

# Harvest all .json sidecars from .ledger/
declare -A current_proofs=()
while IFS= read -r -d $'\0' json_file; do

    # Extract proof stem (filename without .json)
    proof_stem=$(basename "$json_file" .json)

    # Read sidecar
    if ! sidecar=$(cat "$json_file" 2>/dev/null); then
        continue
    fi

    # Get hash.full from sidecar
    sidecar_hash_full=$(echo "$sidecar" | jq -r '.hash.full // ""' 2>/dev/null || echo "")
    if [[ -z "$sidecar_hash_full" ]]; then
        continue
    fi

    # Check if this proof was in the previous ledger entry
    prev_hash_full=$(echo "$PREVIOUS_PROOFS" | jq -r ".[\"$proof_stem\"].hash.full // \"\"" 2>/dev/null || echo "")

    # Determine if proof was re-run or carried forward
    if [[ "$sidecar_hash_full" == "$prev_hash_full" ]] && [[ -n "$prev_hash_full" ]]; then
        # Carry forward from previous entry (hash unchanged, proof not re-run this session)
        proof_entry=$(echo "$PREVIOUS_PROOFS" | jq ".[\"$proof_stem\"]" 2>/dev/null || echo "{}")
    else
        # Use sidecar data (proof was re-run, or is new)
        proof_entry=$(cat "$json_file")
    fi

    current_proofs["$proof_stem"]="$proof_entry"
done < <(find "$PROJECT_ROOT/.ledger" -name "*.json" -print0 2>/dev/null)

# If no proofs at all, exit silently (this commit doesn't touch proofs)
if [[ ${#current_proofs[@]} -eq 0 ]]; then
    exit 0
fi

# Build current proofs JSON object
CURRENT_PROOFS_JSON="{"
first=true
for proof_stem in "${!current_proofs[@]}"; do
    if [[ "$first" == true ]]; then
        first=false
    else
        CURRENT_PROOFS_JSON+=","
    fi
    # Escape the proof stem for JSON (no trailing newline)
    escaped_stem=$(printf '%s' "$proof_stem" | jq -Rs '.')
    CURRENT_PROOFS_JSON+="$escaped_stem:${current_proofs[$proof_stem]}"
done
CURRENT_PROOFS_JSON+="}"

# Compute suite.new, suite.removed, suite.changed
# new: proofs in current but not in previous
# removed: proofs in previous but not in current
# changed: proofs in both but with different hash.full

NEW_PROOFS="[]"
REMOVED_PROOFS="[]"
CHANGED_PROOFS="[]"

# Find new proofs
for proof_stem in "${!current_proofs[@]}"; do
    if ! echo "$PREVIOUS_PROOFS" | jq -e ".[\"$proof_stem\"] != null" >/dev/null 2>&1; then
        NEW_PROOFS=$(echo "$NEW_PROOFS" | jq ".[length] += 1 | .[length-1] = \"$proof_stem\"" 2>/dev/null || echo "[]")
    fi
done

# Find removed proofs and changed proofs
for proof_stem in $(echo "$PREVIOUS_PROOFS" | jq -r 'keys[]' 2>/dev/null || true); do
    if [[ ! -v current_proofs["$proof_stem"] ]]; then
        REMOVED_PROOFS=$(echo "$REMOVED_PROOFS" | jq ".[length] += 1 | .[length-1] = \"$proof_stem\"" 2>/dev/null || echo "[]")
    else
        # Check if hash changed
        prev_full=$(echo "$PREVIOUS_PROOFS" | jq -r ".[\"$proof_stem\"].hash.full // \"\"")
        curr_full=$(echo "${current_proofs[$proof_stem]}" | jq -r '.hash.full // ""' 2>/dev/null || echo "")

        if [[ "$prev_full" != "$curr_full" ]] && [[ -n "$prev_full" ]] && [[ -n "$curr_full" ]]; then
            # Determine which tier changed
            prev_source=$(echo "$PREVIOUS_PROOFS" | jq -r ".[\"$proof_stem\"].hash.source // \"\"")
            prev_deps=$(echo "$PREVIOUS_PROOFS" | jq -r ".[\"$proof_stem\"].hash.deps // \"\"")
            prev_env=$(echo "$PREVIOUS_PROOFS" | jq -r ".[\"$proof_stem\"].hash.env // \"\"")

            curr_source=$(echo "${current_proofs[$proof_stem]}" | jq -r '.hash.source // ""' 2>/dev/null || echo "")
            curr_deps=$(echo "${current_proofs[$proof_stem]}" | jq -r '.hash.deps // ""' 2>/dev/null || echo "")
            curr_env=$(echo "${current_proofs[$proof_stem]}" | jq -r '.hash.env // ""' 2>/dev/null || echo "")

            if [[ "$prev_source" != "$curr_source" ]]; then
                tier="source"
            elif [[ "$prev_deps" != "$curr_deps" ]]; then
                tier="deps"
            elif [[ "$prev_env" != "$curr_env" ]]; then
                tier="env"
            else
                tier="full"
            fi

            change_entry="{\"proof\":\"$proof_stem\",\"tier\":\"$tier\"}"
            CHANGED_PROOFS=$(echo "$CHANGED_PROOFS" | jq ".[length] += 1 | .[length-1] = $change_entry" 2>/dev/null || echo "[]")
        fi
    fi
done

# Build suite metadata
SUITE_JSON=$(jq -n \
    --arg proof_count "$(echo "$CURRENT_PROOFS_JSON" | jq 'length')" \
    --argjson new "$NEW_PROOFS" \
    --argjson removed "$REMOVED_PROOFS" \
    --argjson changed "$CHANGED_PROOFS" \
    '{proof_count: ($proof_count | tonumber), total_assertions: 0, new: $new, removed: $removed, changed: $changed}')

# Build ledger entry
# The proofs object goes in on STDIN, not as --argjson: Linux caps a single
# argv string at MAX_ARG_STRLEN = 128 KiB (independent of ARG_MAX), and the
# proofs object outgrows that as the suite grows ("Argument list too long").
ENTRY=$(printf '%s' "$CURRENT_PROOFS_JSON" | jq -c \
    --arg tree "$TREE" \
    --arg parent_tree "$PARENT_TREE" \
    --arg parent_commit "$CURRENT_COMMIT" \
    --arg branch "$BRANCH" \
    --argjson suite "$SUITE_JSON" \
    '{tree: $tree, parent_tree: $parent_tree, parent_commit: $parent_commit, timestamp: now | strftime("%Y-%m-%dT%H:%M:%SZ"), branch: $branch, proofs: ., suite: $suite}')

# Append to .ledger/index.jsonl
echo "$ENTRY" >> "$PROJECT_ROOT/.ledger/index.jsonl"

# Stage .ledger/index.jsonl
git add "$PROJECT_ROOT/.ledger/index.jsonl"

exit 0

#!/bin/bash
# Finish the DharmaMitra translations with three jobs in parallel.
# Needs DHARMAMITRA_API_KEY in the environment (keyed access is not held to the
# public daily quota; parallel jobs on the public endpoint would just exhaust it).
# Each job writes its own ledger, so they never touch the same file.
# Logs: 0-INBOX/temp/dm-queue/par-*.log
cd "$(dirname "$0")/../../.."
[ -z "$DHARMAMITRA_API_KEY" ] && { echo "set DHARMAMITRA_API_KEY first"; exit 1; }
# Reject a placeholder such as "…" or anything that is not plain ASCII (HTTP headers must be).
if ! LC_ALL=C printf '%s' "$DHARMAMITRA_API_KEY" | grep -qE '^[A-Za-z0-9._~+/=-]+$'; then
  echo "DHARMAMITRA_API_KEY does not look like a real key (placeholder or non-ASCII characters)"; exit 1
fi
DM=4-SYSTEM/Skills/machine-translate/scripts/dm_translate.py
Q=0-INBOX/temp/dm-queue
T=3-TRANSFORMATIONS/Translations/Dharmamitra
RJ=1-SOURCES/Commentaries/bo-rangjung-dorje-tika.md
ROOT=1-SOURCES/Translations/bo-ratnagunasancayagatha.md

track() {  # source label tag trackdir stylefile log
  local common=(--source "$1" --lang "$2" --lang-tag "$3" --out "$4" --style-file "$5" --context-header "$4/context-header.md" --sleep 1)
  python3 $DM "${common[@]}" >> "$6" 2>&1 < /dev/null
  python3 $DM "${common[@]}" --headings --heading-batch 15 --heading-style "$(cat "$4/heading-style.md")" >> "$6" 2>&1 < /dev/null
  echo "JOB DONE $(date '+%F %T')" >> "$6"
}

# 1. Rangjung Dorje -> English: the remaining ~33 blocks, then the 317 TOC headings
track $RJ english en $T/en-commentaries $T/en-commentaries/style-bo-rangjung-dorje-tika.md $Q/par-rangjung-en.log &
# 2. Rangjung Dorje -> Chinese: all 323 blocks, then the 317 TOC headings
track $RJ "modern chinese" zh $T/zh-commentaries $T/zh-commentaries/style-bo-rangjung-dorje-tika.md $Q/par-rangjung-zh.log &
# 3. Root English: re-translate, one verse per call, the 12 verses whose lines were merged
( python3 $DM --source $ROOT --lang english --lang-tag en --out $T/en --style-file $T/en/style.md \
    --context-header $T/en/context-header.md --batch 1 --force --sleep 1 \
    --only 4-54,4-63,4-74,4-87,5-7,5-23,5-24,5-52,5-82,5-105,5-109,8-4 >> $Q/par-root-repair.log 2>&1 < /dev/null
  echo "JOB DONE $(date '+%F %T')" >> $Q/par-root-repair.log ) &

wait
echo "all three jobs finished: $(date '+%F %T')"

#!/bin/bash
# Re-translate, one block per call, the blocks where DharmaMitra left Tibetan untranslated
# (found by the post-run check on 2026-10-04). Needs DHARMAMITRA_API_KEY.
cd "$(dirname "$0")/../../.."
[ -z "$DHARMAMITRA_API_KEY" ] && { echo "set DHARMAMITRA_API_KEY first"; exit 1; }
if ! LC_ALL=C printf '%s' "$DHARMAMITRA_API_KEY" | grep -qE '^[A-Za-z0-9._~+/=-]+$'; then
  echo "DHARMAMITRA_API_KEY does not look like a real key (placeholder or non-ASCII characters)"; exit 1
fi
DM=4-SYSTEM/Skills/machine-translate/scripts/dm_translate.py
LOG=0-INBOX/temp/dm-queue/repair.log
T=3-TRANSFORMATIONS/Translations/Dharmamitra

fix() {  # source label tag trackdir stylefile ids
  python3 $DM --source "$1" --lang "$2" --lang-tag "$3" --out "$4" --style-file "$5" \
    --context-header "$4/context-header.md" --batch 1 --force --sleep 1 --only "$6" >> $LOG 2>&1 < /dev/null
}

fix 1-SOURCES/Commentaries/bo-mipham-lekshe.md "modern chinese" zh $T/zh-commentaries \
    $T/zh-commentaries/style-bo-mipham-lekshe.md 1-94,1-95,1-96,1-98,1-99,1-101,1-102
fix 1-SOURCES/Commentaries/bo-rangjung-dorje-tika.md english en $T/en-commentaries \
    $T/en-commentaries/style-bo-rangjung-dorje-tika.md 2-104
echo "REPAIR DONE $(date '+%F %T')" >> $LOG
tail -25 $LOG

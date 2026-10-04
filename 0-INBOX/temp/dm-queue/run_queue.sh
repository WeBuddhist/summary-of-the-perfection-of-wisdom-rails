#!/bin/bash
# Sequential DharmaMitra queue (never parallel: shared daily quota).
# Each line of queue.txt (TAB-separated): source, lang-label, lang-tag, track-dir, style-file
# Every step runs blocks then headings (batched); stops the whole queue on a daily-quota hit.
cd "$(dirname "$0")/../../.."
DM=4-SYSTEM/Skills/machine-translate/scripts/dm_translate.py
LOG=0-INBOX/temp/dm-queue/queue.log
while IFS=$'\t' read -r src lang tag track style; do
  [ -z "$src" ] && continue; case "$src" in \#*) continue;; esac
  echo "=== $(date '+%F %T') $src -> $tag" >> $LOG
  common=(--source "$src" --lang "$lang" --lang-tag "$tag" --out "$track" --style-file "$style" --context-header "$track/context-header.md")
  python3 $DM "${common[@]}" >> $LOG 2>&1 < /dev/null
  if tail -40 $LOG | grep -qi 'daily quota'; then echo "QUOTA STOP $(date '+%F %T')" >> $LOG; exit 3; fi
  python3 $DM "${common[@]}" --headings --heading-batch 15 --heading-style "$(cat $track/heading-style.md)" >> $LOG 2>&1 < /dev/null
  if tail -40 $LOG | grep -qi 'daily quota'; then echo "QUOTA STOP $(date '+%F %T')" >> $LOG; exit 3; fi
done < 0-INBOX/temp/dm-queue/queue.txt
echo "QUEUE DONE $(date '+%F %T')" >> $LOG

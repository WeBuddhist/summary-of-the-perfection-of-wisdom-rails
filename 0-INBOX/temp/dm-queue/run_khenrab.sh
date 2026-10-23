#!/bin/bash
# Khenrab Jamyang commentary -> one language (blocks, then TOC headings). Needs DHARMAMITRA_API_KEY.
# usage: run_khenrab.sh <label> <tag> <track-subdir>
cd "$(dirname "$0")/../../.."
DM=4-SYSTEM/Skills/machine-translate/scripts/dm_translate.py
T=3-TRANSFORMATIONS/Translations/Dharmamitra/$3
SRC=1-SOURCES/Commentaries/bo-khenrab-jamyang-norbu-dronme.md
LOG=0-INBOX/temp/dm-queue/khenrab-$2.log
common=(--source $SRC --lang "$1" --lang-tag $2 --out $T --style-file $T/style-bo-khenrab-jamyang-norbu-dronme.md --context-header $T/context-header.md --sleep 1)
python3 $DM "${common[@]}" >> $LOG 2>&1 < /dev/null
python3 $DM "${common[@]}" --headings --heading-batch 15 --heading-style "$(cat $T/heading-style.md)" >> $LOG 2>&1 < /dev/null
echo "JOB DONE $(date '+%F %T')" >> $LOG

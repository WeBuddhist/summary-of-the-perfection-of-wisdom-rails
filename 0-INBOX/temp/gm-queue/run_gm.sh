#!/bin/bash
# Gemini zero-shot baseline for one (source, language) pair: blocks, then TOC headings.
# Resumable (append-only ledger); retries a pass up to 5 times while blocks remain.
# usage: run_gm.sh <source> <label> <tag> <track-subdir> <style-file> <logname>
cd "$(dirname "$0")/../../.."
source ~/.zshrc >/dev/null 2>&1
GM=4-SYSTEM/Skills/machine-translate/scripts/gm_translate.py
T=3-TRANSFORMATIONS/Translations/Gemini/$4
LOG=0-INBOX/temp/gm-queue/$6.log
common=(--source "$1" --lang "$2" --lang-tag "$3" --out "$T" --style-file "$5" --context-header "$T/context-header.md" --sleep 1 "${@:7}")
for mode in blocks headings; do
  extra=(); [ $mode = headings ] && extra=(--headings)
  for i in 1 2 3 4 5; do
    echo "=== $mode pass $i $(date '+%F %T')" >> $LOG
    python3 $GM "${common[@]}" "${extra[@]}" >> $LOG 2>&1 < /dev/null
    last=$(grep '^SUMMARY' $LOG | tail -1)
    echo "$last" | grep -q '"stopped_at": null' && echo "$last" | grep -q '"failed": \[\]' && break
    sleep 30
  done
done
echo "JOB DONE $(date '+%F %T')" >> $LOG

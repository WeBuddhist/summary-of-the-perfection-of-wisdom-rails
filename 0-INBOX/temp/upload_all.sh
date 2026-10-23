#!/bin/bash
# Upload the rest of the Phakpa Düpa set to library.webuddhist.com, in dependency order.
# The Sanskrit root is already live (text 415kqyNhR8qC6d7R1dhpB).
#
# Each step: live dry run (aborts on any failed check) -> you press Enter -> --execute -> --verify.
# Ids are patched into each file's frontmatter after every call, and steps already done are
# skipped on a re-run, so it is safe to stop and start again.
#
#   0-INBOX/temp/upload_all.sh            # all steps, asking before each --execute
#   0-INBOX/temp/upload_all.sh 3          # start from step 3
#   YES=1 0-INBOX/temp/upload_all.sh      # no prompts (your one confirmation for the whole run)
#
# Credentials: read from Dzongsar-dolma-bumtsok-rails/4-SYSTEM/scripts/.env (never copied here).
set -e
cd "$(dirname "$0")/../.."
set -a; source ../Dzongsar-dolma-bumtsok-rails/4-SYSTEM/scripts/.env; set +a
LOG=0-INBOX/temp/upload_all.log
START=${1:-1}

ROOT_UP=4-SYSTEM/Skills/root-text-upload/scripts/upload_root_text.py
COMM_UP=4-SYSTEM/Skills/commentary-upload/scripts/upload_commentary.py
TR_UP=4-SYSTEM/Skills/translation-upload/scripts/upload_translation.py
T=3-TRANSFORMATIONS/Translations/Dharmamitra

# step  uploader  file  extra-flags  description
STEPS=(
  "$TR_UP|1-SOURCES/Translations/bo-ratnagunasancayagatha.md|--alignment transclusion|Tibetan, translation of the Sanskrit"
  "$TR_UP|1-SOURCES/Translations/zh-ratnagunasancayagatha.md|--alignment transclusion|Chinese, translation of the Tibetan"
  "$COMM_UP|1-SOURCES/Commentaries/bo-mipham-lekshe.md||Mipham commentary, commentary of the Tibetan"
  "$COMM_UP|1-SOURCES/Commentaries/bo-rangjung-dorje-tika.md||Rangjung Dorje tika, commentary of the Tibetan"
  "$TR_UP|$T/en/bo-ratnagunasancayagatha-en.md||English root (DharmaMitra), translation of the Tibetan"
  "$TR_UP|$T/en-commentaries/bo-mipham-lekshe-en.md||Mipham English (DharmaMitra)"
  "$TR_UP|$T/zh-commentaries/bo-mipham-lekshe-zh.md||Mipham Chinese (DharmaMitra)"
  "$TR_UP|$T/en-commentaries/bo-rangjung-dorje-tika-en.md||Rangjung Dorje English (DharmaMitra)"
  "$TR_UP|$T/zh-commentaries/bo-rangjung-dorje-tika-zh.md||Rangjung Dorje Chinese (DharmaMitra)"
)

n=0
for s in "${STEPS[@]}"; do
  n=$((n+1)); [ $n -lt $START ] && continue
  IFS='|' read -r up file flags desc <<< "$s"
  echo; echo "################ step $n/${#STEPS[@]}: $desc" | tee -a $LOG
  echo "--- dry run" | tee -a $LOG
  python3 $up "$file" $flags 2>&1 | grep -v '^  INFO' | tee -a $LOG | sed -n '/== checks/,$p'
  [ ${PIPESTATUS[0]} -ne 0 ] && { echo "ABORTED at step $n (dry run failed) — fix and re-run: $0 $n" | tee -a $LOG; exit 1; }
  if [ -z "$YES" ]; then read -r -p "Execute step $n ($desc)? [Enter = yes, Ctrl-C = stop] " _; fi
  echo "--- execute" | tee -a $LOG
  python3 $up "$file" $flags --execute --skip-lint 2>&1 | grep -v '^  INFO' | tee -a $LOG | sed -n '/== EXECUTE/,$p'
  [ ${PIPESTATUS[0]} -ne 0 ] && { echo "ABORTED at step $n (execute failed) — ids so far are in the file; re-run: $0 $n" | tee -a $LOG; exit 1; }
  echo "--- verify" | tee -a $LOG
  python3 $up "$file" $flags --verify 2>&1 | tee -a $LOG | tail -8
done
echo; echo "ALL UPLOADS DONE $(date '+%F %T')" | tee -a $LOG

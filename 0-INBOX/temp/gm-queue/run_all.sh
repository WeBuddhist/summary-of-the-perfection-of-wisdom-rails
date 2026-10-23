#!/bin/bash
# Launch all seven Gemini tracks in parallel (detached). Logs in 0-INBOX/temp/gm-queue/*.log
cd "$(dirname "$0")/../../.."
R=0-INBOX/temp/gm-queue/run_gm.sh
G=3-TRANSFORMATIONS/Translations/Gemini
ROOT=1-SOURCES/Translations/bo-ratnagunasancayagatha.md
C=1-SOURCES/Commentaries
nohup $R $ROOT english en en $G/en/style.md root-en >/dev/null 2>&1 &
nohup $R $ROOT "modern chinese" zh zh $G/zh/style.md root-zh >/dev/null 2>&1 &
for c in mipham-lekshe rangjung-dorje-tika khenrab-jamyang-norbu-dronme; do
  nohup $R $C/bo-$c.md english en en-commentaries $G/en-commentaries/style-bo-$c.md $c-en --cross-headings >/dev/null 2>&1 &
  nohup $R $C/bo-$c.md "modern chinese" zh zh-commentaries $G/zh-commentaries/style-bo-$c.md $c-zh --cross-headings >/dev/null 2>&1 &
done

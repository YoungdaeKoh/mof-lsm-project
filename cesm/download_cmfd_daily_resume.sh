#!/bin/bash
# CMFD v2.0 daily resume downloader.
# 8 vars x 74 yr (1951-2024) = 592 files via per-file wget -c (resume-safe).
# Replaces the unstable `wget -r` whole-dir crawl that kept getting
# "Error in server response. Closing." from the TPDC FTP server.
set -u

DEST=/data2/ydkoh/CMFD_daily
LIST=/data2/ydkoh/cmfd_all.txt
BASE="ftp://download_4545878:17766766@ftp2.tpdc.ac.cn:6201/Data_forcing_01dy_010deg"
LOG=/data2/ydkoh/cmfd_daily_resume.log

cd "$DEST" || exit 1
echo "==== RESUME START $(date '+%F %T') ====" >> "$LOG"

# Multiple rounds: the FTP server drops connections intermittently, so a single
# pass leaves gaps. Re-run until nothing is missing (max 8 rounds).
for round in $(seq 1 8); do
  missing=0
  while read -r f; do
    [ -z "$f" ] && continue
    # -c resumes partial files; if already complete, wget reports nothing to do.
    wget -c --tries=10 --timeout=90 --waitretry=15 --no-verbose \
      -a "$LOG" "$BASE/$f"
    if [ ! -s "$f" ]; then
      missing=$((missing + 1))
    fi
  done < "$LIST"
  have=$(ls -1 *.nc 2>/dev/null | wc -l)
  echo "---- ROUND $round done $(date '+%F %T')  have=$have / 592  still_missing(by -s)=$missing ----" >> "$LOG"
  [ "$missing" -eq 0 ] && break
done

echo "==== ALL DONE $(date '+%F %T')  files: $(ls -1 *.nc 2>/dev/null | wc -l) / 592 ====" >> "$LOG"

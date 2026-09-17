#!/usr/bin/env bash
# ---------------------------------------------------------------
# Facebook Page par post bhejne wali script.
#
# Agar FB_PAGE_ID / FB_ACCESS_TOKEN mojood na hoon to script
# DRY RUN mode mein chalti hai: sirf dikhati hai ke kya post hota,
# asal mein Facebook ko kuch nahi bhejti.
# ---------------------------------------------------------------

set -euo pipefail

# ---- 1. Post ka message tayyar karo ----------------------------
# Yahan aap kuch bhi bana sakte hain: date, mausam, rate, wagera.
TODAY=$(date -u '+%d %B %Y')
TIME_UTC=$(date -u '+%H:%M')

MESSAGE="Assalam-o-Alaikum!

Ye post GitHub Actions ne khud bheji hai.
Tareekh: ${TODAY}
Waqt (UTC): ${TIME_UTC}

#automation #githubactions"

echo "=============================================="
echo " POST KA MATN:"
echo "=============================================="
echo "$MESSAGE"
echo "=============================================="
echo ""

# ---- 2. Dekho ke token mojood hai ya nahi ----------------------
PAGE_ID="${FB_PAGE_ID:-}"
TOKEN="${FB_ACCESS_TOKEN:-}"

if [ -z "$PAGE_ID" ] || [ -z "$TOKEN" ]; then
  echo "DRY RUN: FB_PAGE_ID ya FB_ACCESS_TOKEN set nahi hai."
  echo "Is liye Facebook ko kuch nahi bheja gaya."
  echo ""
  echo "Asli posting ke liye GitHub repo mein:"
  echo "  Settings > Secrets and variables > Actions"
  echo "  mein FB_PAGE_ID aur FB_ACCESS_TOKEN add karein."
  exit 0
fi

# ---- 3. Asli post bhejo ----------------------------------------
echo "LIVE: Facebook Page (${PAGE_ID}) par post bheji ja rahi hai..."

RESPONSE=$(curl -s -X POST \
  "https://graph.facebook.com/v21.0/${PAGE_ID}/feed" \
  --data-urlencode "message=${MESSAGE}" \
  --data-urlencode "access_token=${TOKEN}")

echo "Facebook ka jawab: ${RESPONSE}"

# Agar jawab mein "error" aaya to job ko fail kar do
if echo "$RESPONSE" | grep -q '"error"'; then
  echo "Post fail ho gayi."
  exit 1
fi

echo "Post kamyabi se chali gayi."

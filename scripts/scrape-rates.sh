#!/usr/bin/env bash
# ---------------------------------------------------------------
# Roz ka currency rate utha kar CSV mein jama karta hai.
#
# Source : open.er-api.com  (bilkul free, koi API key nahi)
# Output : data/rates.csv
#
# Har din ek nayi line barhti hai. Mahine baad aap ke paas
# poora record hota hai jis se graph bhi ban sakta hai.
# ---------------------------------------------------------------

set -euo pipefail

API_URL="https://open.er-api.com/v6/latest/USD"
CSV_FILE="data/rates.csv"
TODAY=$(date -u '+%Y-%m-%d')

echo "==> Rate la rahe hain: $API_URL"

# ---- 1. Data download karo -------------------------------------
JSON=$(curl -s --max-time 30 --retry 3 --retry-delay 5 "$API_URL")

if [ -z "$JSON" ]; then
  echo "ERROR: API se kuch nahi mila (internet ya server ka masla)."
  exit 1
fi

# ---- 2. Check karo ke jawab sahi hai ---------------------------
if ! echo "$JSON" | grep -q '"result":"success"'; then
  echo "ERROR: API ne success nahi bheja. Jawab:"
  echo "$JSON" | head -c 400
  exit 1
fi

# ---- 3. JSON se qeematein nikalo -------------------------------
# get_rate <CODE>  ->  us currency ki value (USD ke muqable)
get_rate() {
  echo "$JSON" | grep -o "\"$1\":[0-9.]*" | head -1 | cut -d: -f2
}

PKR=$(get_rate PKR)
GBP=$(get_rate GBP)
EUR=$(get_rate EUR)
SAR=$(get_rate SAR)
AED=$(get_rate AED)

# Agar PKR hi na mila to aage barhne ka faida nahi
if [ -z "$PKR" ]; then
  echo "ERROR: PKR ka rate nahi mil saka."
  exit 1
fi

# API ka apna update time
UPDATED=$(echo "$JSON" | grep -o '"time_last_update_utc":"[^"]*"' | cut -d'"' -f4)

# ---- 4. Hisaab: 1 GBP = kitne PKR? -----------------------------
# API sab kuch USD ke muqable deti hai, to taqseem karni parti hai.
calc() {
  awk -v p="$PKR" -v x="$1" 'BEGIN { if (x+0 == 0) print ""; else printf "%.4f", p/x }'
}

USD_PKR=$(awk -v p="$PKR" 'BEGIN { printf "%.4f", p }')
GBP_PKR=$(calc "$GBP")
EUR_PKR=$(calc "$EUR")
SAR_PKR=$(calc "$SAR")
AED_PKR=$(calc "$AED")

echo ""
echo "  Tareekh   : $TODAY"
echo "  1 USD     = $USD_PKR PKR"
echo "  1 GBP     = $GBP_PKR PKR"
echo "  1 EUR     = $EUR_PKR PKR"
echo "  1 SAR     = $SAR_PKR PKR"
echo "  1 AED     = $AED_PKR PKR"
echo "  Source ka update: $UPDATED"
echo ""

# ---- 5. CSV mein likho -----------------------------------------
mkdir -p "$(dirname "$CSV_FILE")"

# File pehli baar ban rahi hai? To header daalo.
if [ ! -f "$CSV_FILE" ]; then
  echo "date,usd_pkr,gbp_pkr,eur_pkr,sar_pkr,aed_pkr,source_updated_utc" > "$CSV_FILE"
  echo "==> Nayi CSV bana di (header ke sath)."
fi

# Aaj ki line pehle se mojood hai? To dobara mat likho.
# (Workflow do baar chal jaye to duplicate na bane.)
if cut -d, -f1 "$CSV_FILE" | grep -qx "$TODAY"; then
  echo "==> $TODAY ka record pehle se mojood hai. Kuch nahi badla."
  exit 0
fi

echo "${TODAY},${USD_PKR},${GBP_PKR},${EUR_PKR},${SAR_PKR},${AED_PKR},\"${UPDATED}\"" >> "$CSV_FILE"
echo "==> Nayi line CSV mein likh di."

# ---- 6. Poori file dikhao (akhri 10 din) -----------------------
echo ""
echo "===== $CSV_FILE (akhri 10 lines) ====="
tail -10 "$CSV_FILE"

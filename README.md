# Facebook Scheduled Post — Demo

Ye ek chhota sa demo hai jo samjhata hai ke **GitHub Actions** kaise
ek muqarrara waqt par khud-ba-khud kaam karta hai.

## Files ka matlab

```
fb-post-demo/
├─ .github/
│  └─ workflows/
│     └─ fb-post.yml     <-- GitHub ko batata hai: KAB chalna hai, KYA karna hai
├─ scripts/
│  └─ post.sh            <-- Asli kaam: message banata hai aur Facebook ko bhejta hai
└─ README.md
```

Yaad rakhein: workflow file **hamesha** `.github/workflows/` ke andar honi chahiye,
warna GitHub use pehchanta hi nahi.

## Do modes

| Mode | Kab | Kya hota hai |
|---|---|---|
| **DRY RUN** | Jab Secrets set na hoon | Sirf dikhata hai ke kya post hoti. Facebook ko kuch nahi jata. **Seekhne ke liye yehi use karein.** |
| **LIVE** | Jab Secrets set hoon | Facebook Page par asli post chali jati hai |

## Chalane ka tareeqa

### 1. Apne computer par test (abhi, bina GitHub ke)

```bash
bash scripts/post.sh
```

DRY RUN chalega aur post ka matn screen par dikh jayega.

### 2. GitHub par

```bash
git remote add origin https://github.com/<aap-ka-username>/fb-post-demo.git
git branch -M main
git push -u origin main
```

Phir GitHub par:

1. Repo kholein → upar **Actions** tab par click karein
2. Left side "Facebook Scheduled Post" dikhega → us par click
3. Dayein taraf **Run workflow** ka button → daba dein
4. Thori der mein job chalti dikhegi — click kar ke uske andar logs dekh sakte hain

Yahi wo jagah hai jahan aap asal mein "working" dekhenge.

### 3. Asli Facebook post ke liye (baad mein)

Repo → **Settings → Secrets and variables → Actions → New repository secret**

| Naam | Value |
|---|---|
| `FB_PAGE_ID` | Aap ke Facebook **Page** ki ID |
| `FB_ACCESS_TOKEN` | Page Access Token (Meta Developer se) |

Ye add karte hi script khud LIVE mode mein chali jayegi — code badalne ki
zaroorat nahi.

> Note: API se sirf **Facebook Page** par post hoti hai, personal profile par nahi.

## Time badalna ho to

`fb-post.yml` mein cron line badlein. Cron **UTC** mein hai, Pakistan UTC+5 hai:

| Pakistan ka waqt | Cron (UTC) |
|---|---|
| 9:00 AM | `0 4 * * *` |
| 1:00 PM | `0 8 * * *` |
| 8:00 PM | `0 15 * * *` |
| Har Juma 5 PM | `0 12 * * 5` |

## Zaroori khamiyan

- GitHub ka cron **5–30 minute late** ho sakta hai. Bilkul sharp waqt ki guarantee nahi.
- Public repo 60 din tak khali pari rahe to GitHub schedule **khud band** kar deta hai.
- Facebook Page token ~60 din baad expire hota hai, phir renew karna parta hai.

---

# Demo 2 — Daily Rate Scraper (koi API key nahi)

Ye demo rozana currency rate utha kar `data/rates.csv` mein jama karta hai,
aur us file ko **khud repo mein commit** kar deta hai. Yani GitHub hi aap ka
database ban jata hai.

## Files

```
scripts/scrape-rates.sh              <-- rate laata hai, CSV mein likhta hai
.github/workflows/scrape-rates.yml   <-- roz 8 AM (PKT) chalata hai + commit karta hai
data/rates.csv                       <-- jama shuda record (roz ek line barhti hai)
```

## Data kahan se aata hai

`https://open.er-api.com/v6/latest/USD` — bilkul free, **koi API key nahi chahiye**.

## CSV kaisi dikhti hai

```csv
date,usd_pkr,gbp_pkr,eur_pkr,sar_pkr,aed_pkr,source_updated_utc
2026-09-17,277.5103,372.5326,319.2357,74.0027,75.5644,"Thu, 17 Sep 2026 00:02:31 +0000"
```

Har din ek nayi line. Ek mahine baad 30 lines — phir aap Excel mein khol kar
graph bana sakte hain ke dollar kaise charha ya gira.

## Khud chala kar dekhein

```bash
bash scripts/scrape-rates.sh
```

Dobara chalayein — wo kahega "aaj ka record pehle se mojood hai" aur duplicate
line nahi banayega.

## GitHub par

Push karne ke baad: **Actions** tab -> "Daily Rate Scraper" -> **Run workflow**

Job chalne ke baad repo mein dekhein — `data/rates.csv` khud update ho chuki hogi,
aur commits mein "Rate update: 2026-09-17" wala commit **github-actions[bot]** ke
naam se nazar aayega. Wo commit aap ne nahi kiya — robot ne kiya.

## Do ahem baatein

**1. `permissions: contents: write`**

Workflow mein ye line zaroori hai. Iske baghair Actions repo mein likh nahi sakta
aur push fail ho jata hai. Ye sab se aam ghalti hai.

**2. Sirf tabdeeli par commit**

```bash
if git diff --quiet -- data/rates.csv; then
  exit 0      # kuch nahi badla, commit mat karo
fi
```

Warna har roz khali commit banta rahega.

## Kisi aur cheez ka rate chahiye?

`scripts/scrape-rates.sh` mein `API_URL` badal dein. Wohi tareeqa:
data laao -> qeemat nikalo -> CSV mein line barhao.

Misaal: mausam (open-meteo.com), crypto (coingecko), ya kisi bhi site ka HTML.

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

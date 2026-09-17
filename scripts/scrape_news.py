#!/usr/bin/env python3
"""
Roz ki news headlines RSS feeds se utha kar jama karta hai.

Output do jagah jata hai:
  data/news.csv              -> sari headlines ka permanent record
  data/news/YYYY-MM-DD.md    -> us din ka parhne laiq digest

Koi API key nahi chahiye. RSS feeds publicly available hain.
"""

import csv
import os
import sys
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ---- Yahan se news sources badal sakte hain -----------------------
SOURCES = [
    ("Dawn",     "https://www.dawn.com/feeds/home"),
    ("BBC Urdu", "https://feeds.bbci.co.uk/urdu/rss.xml"),
    ("Geo",      "https://www.geo.tv/rss/1/1"),
]

CSV_FILE = "data/news.csv"
DIGEST_DIR = "data/news"
MAX_PER_SOURCE = 15          # har source se zyada se zyada kitni khabrein
HEADERS = ["collected_utc", "source", "published", "title", "link"]

UA = "Mozilla/5.0 (compatible; news-scraper/1.0; +https://github.com)"


def fetch(url, timeout=30):
    """Feed download karo. Nakami par None."""
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean(text):
    """Extra spaces/newlines hata do taake CSV saaf rahe."""
    if text is None:
        return ""
    return " ".join(text.split()).strip()


def parse_items(xml_bytes, limit):
    """RSS ya Atom se (title, link, published) nikalo."""
    root = ET.fromstring(xml_bytes)
    items = []

    # RSS 2.0
    for item in root.iter("item"):
        items.append((
            clean(item.findtext("title")),
            clean(item.findtext("link")),
            clean(item.findtext("pubDate")),
        ))

    # Atom (agar RSS items na milein)
    if not items:
        ns = "{http://www.w3.org/2005/Atom}"
        for entry in root.iter(ns + "entry"):
            link_el = entry.find(ns + "link")
            items.append((
                clean(entry.findtext(ns + "title")),
                clean(link_el.get("href")) if link_el is not None else "",
                clean(entry.findtext(ns + "updated")),
            ))

    # Sirf wo jin ka title aur link dono mojood hon
    items = [i for i in items if i[0] and i[1]]
    return items[:limit]


def load_seen_links(path):
    """Pehle se jama shuda links, taake wohi khabar dobara na aaye."""
    seen = set()
    if not os.path.exists(path):
        return seen
    with open(path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            link = row.get("link")
            if link:
                seen.add(link)
    return seen


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    today = now.strftime("%Y-%m-%d")

    os.makedirs("data", exist_ok=True)
    os.makedirs(DIGEST_DIR, exist_ok=True)

    seen = load_seen_links(CSV_FILE)
    print(f"==> Pehle se jama shuda khabrein: {len(seen)}")

    new_rows = []
    failures = []

    for name, url in SOURCES:
        print(f"\n==> {name}: {url}")
        try:
            items = parse_items(fetch(url), MAX_PER_SOURCE)
        except (urllib.error.URLError, ET.ParseError, OSError) as e:
            # Ek source fail ho to baqi chalti rahein
            print(f"    NAKAM: {type(e).__name__}: {e}")
            failures.append(name)
            continue

        fresh = 0
        for title, link, published in items:
            if link in seen:
                continue
            seen.add(link)
            new_rows.append([stamp, name, published, title, link])
            fresh += 1

        print(f"    Feed mein {len(items)} khabrein | nayi: {fresh}")

    # ---- Sab sources fail ho gaye? To job fail karo --------------
    if len(failures) == len(SOURCES):
        print("\nERROR: koi bhi feed nahi chali.")
        return 1

    if not new_rows:
        print("\n==> Koi nayi khabar nahi mili. CSV waisi hi rahegi.")
        return 0

    # ---- CSV mein likho ------------------------------------------
    is_new_file = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        if is_new_file:
            writer.writerow(HEADERS)
            print(f"\n==> Nayi CSV bana di: {CSV_FILE}")
        writer.writerows(new_rows)

    print(f"\n==> {len(new_rows)} nayi khabrein CSV mein likh di gayin.")

    # ---- Aaj ka digest (markdown) --------------------------------
    digest_path = os.path.join(DIGEST_DIR, f"{today}.md")
    by_source = {}
    for row in new_rows:
        by_source.setdefault(row[1], []).append(row)

    # Append mode: din mein kai baar chale to neeche barhta jaye
    exists = os.path.exists(digest_path)
    with open(digest_path, "a", encoding="utf-8") as f:
        if not exists:
            f.write(f"# Khabrein — {today}\n")
        f.write(f"\n_Jama kiya gaya: {stamp}_\n")
        for name, rows in by_source.items():
            f.write(f"\n## {name}\n\n")
            for _, _, published, title, link in rows:
                f.write(f"- [{title}]({link})\n")

    print(f"==> Digest likh diya: {digest_path}")

    if failures:
        print(f"\nNote: ye sources nakam rahe: {', '.join(failures)}")

    # ---- Screen par jhalak ---------------------------------------
    print("\n===== NAYI SURKHIYAN (pehli 10) =====")
    for _, name, _, title, _ in new_rows[:10]:
        print(f"  [{name}] {title}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

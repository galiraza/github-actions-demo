#!/usr/bin/env python3
"""
Roz ki news RSS se uthata hai - headline AUR poora article content.

Output teen jagah:
  data/news.csv                        -> index (title, link, lafzon ki ginti, file ka pata)
  data/articles/YYYY-MM-DD/<naam>.md   -> har article ka poora matn
  data/news/YYYY-MM-DD.md              -> us din ka digest (links ke sath)

Zaroori: pip install trafilatura
"""

import csv
import hashlib
import os
import re
import sys
import time
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import trafilatura

# ---- Yahan se news sources badal sakte hain -----------------------
SOURCES = [
    ("Dawn",     "https://www.dawn.com/feeds/home"),
    ("BBC Urdu", "https://feeds.bbci.co.uk/urdu/rss.xml"),
    ("Geo",      "https://www.geo.tv/rss/1/1"),
]

CSV_FILE = "data/news.csv"
DIGEST_DIR = "data/news"
ARTICLE_DIR = "data/articles"

MAX_PER_SOURCE = 10      # har source se zyada se zyada kitni khabrein
REQUEST_DELAY = 1.5      # har article ke beech itne second rukna (tehzeeb)
MIN_WORDS = 40           # is se chhota matn "nakam" samjha jayega

HEADERS = ["collected_utc", "source", "published", "title", "link", "words", "file"]

UA = "Mozilla/5.0 (compatible; news-archiver/1.0)"


def fetch(url, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def clean(text):
    return " ".join(text.split()).strip() if text else ""


def parse_items(xml_bytes, limit):
    """RSS ya Atom se (title, link, published) nikalo."""
    root = ET.fromstring(xml_bytes)
    items = []

    for item in root.iter("item"):                       # RSS 2.0
        items.append((
            clean(item.findtext("title")),
            clean(item.findtext("link")),
            clean(item.findtext("pubDate")),
        ))

    if not items:                                        # Atom
        ns = "{http://www.w3.org/2005/Atom}"
        for entry in root.iter(ns + "entry"):
            link_el = entry.find(ns + "link")
            items.append((
                clean(entry.findtext(ns + "title")),
                clean(link_el.get("href")) if link_el is not None else "",
                clean(entry.findtext(ns + "updated")),
            ))

    items = [i for i in items if i[0] and i[1]]
    return items[:limit]


def slugify(source, link, title):
    """File ka mehfooz naam banao: source + title ka tukra + link ka hash."""
    src = re.sub(r"[^a-z0-9]+", "-", source.lower()).strip("-")
    words = re.sub(r"[^a-zA-Z0-9\s-]", "", title).split()[:6]
    tail = "-".join(w.lower() for w in words)
    # Urdu titles se ascii kuch nahi bachta - us surat mein sirf hash
    digest = hashlib.sha1(link.encode("utf-8")).hexdigest()[:8]
    name = f"{src}-{tail}-{digest}" if tail else f"{src}-{digest}"
    return name[:80].strip("-") + ".md"


def get_article_text(link):
    """Article ka asal matn nikalo. Nakami par (None, wajah)."""
    try:
        html = trafilatura.fetch_url(link)
    except Exception as e:
        return None, f"download nakam: {type(e).__name__}"

    if not html:
        return None, "download nakam: khali jawab"

    text = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        include_images=False,
    )

    if not text:
        return None, "matn nahi mila (shayad paywall ya video page)"
    if len(text.split()) < MIN_WORDS:
        return None, f"matn bohot chhota ({len(text.split())} lafz)"

    return text, None


def load_seen_links(path):
    """Pehle se jama shuda links + header ka check."""
    seen = set()
    if not os.path.exists(path):
        return seen

    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return seen

        if header != HEADERS:
            # Purani CSV naye columns se mel nahi khati.
            raise SystemExit(
                f"\nERROR: {path} ka format purana hai.\n"
                f"  Mojooda : {header}\n"
                f"  Darkaar : {HEADERS}\n"
                f"Hal: purani file ka backup le kar usay delete kar dein.\n"
            )

        link_idx = HEADERS.index("link")
        for row in reader:
            if len(row) > link_idx and row[link_idx]:
                seen.add(row[link_idx])

    return seen


def main():
    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    today = now.strftime("%Y-%m-%d")

    day_dir = os.path.join(ARTICLE_DIR, today)
    os.makedirs("data", exist_ok=True)
    os.makedirs(DIGEST_DIR, exist_ok=True)
    os.makedirs(day_dir, exist_ok=True)

    seen = load_seen_links(CSV_FILE)
    print(f"==> Pehle se jama shuda khabrein: {len(seen)}")

    # ---- 1. Sab feeds se nayi khabron ki list banao --------------
    pending = []
    failures = []

    for name, url in SOURCES:
        print(f"\n==> Feed: {name}")
        try:
            items = parse_items(fetch(url), MAX_PER_SOURCE)
        except (urllib.error.URLError, ET.ParseError, OSError) as e:
            print(f"    NAKAM: {type(e).__name__}: {e}")
            failures.append(name)
            continue

        fresh = 0
        for title, link, published in items:
            if link in seen:
                continue
            seen.add(link)
            pending.append((name, title, link, published))
            fresh += 1

        print(f"    feed mein {len(items)} | nayi {fresh}")

    if len(failures) == len(SOURCES):
        print("\nERROR: koi bhi feed nahi chali.")
        return 1

    if not pending:
        print("\n==> Koi nayi khabar nahi. Kuch nahi badla.")
        return 0

    # ---- 2. Har nayi khabar ka poora content laao ----------------
    print(f"\n==> {len(pending)} articles ka content la rahe hain...")
    print(f"    (har ek ke beech {REQUEST_DELAY}s ka waqfa - server par bojh na parey)\n")

    new_rows = []
    no_content = 0

    for i, (source, title, link, published) in enumerate(pending, 1):
        if i > 1:
            time.sleep(REQUEST_DELAY)

        text, why = get_article_text(link)

        if text is None:
            print(f"  [{i}/{len(pending)}] SKIP  {source}: {why}")
            # Article na mile to bhi headline record mein rehti hai
            new_rows.append([stamp, source, published, title, link, 0, ""])
            no_content += 1
            continue

        filename = slugify(source, link, title)
        path = os.path.join(day_dir, filename)

        with open(path, "w", encoding="utf-8") as f:
            f.write(f"# {title}\n\n")
            f.write(f"- Source: {source}\n")
            f.write(f"- Published: {published}\n")
            f.write(f"- Link: {link}\n")
            f.write(f"- Collected: {stamp}\n\n---\n\n")
            f.write(text.strip() + "\n")

        words = len(text.split())
        new_rows.append([stamp, source, published, title, link, words, path.replace("\\", "/")])
        print(f"  [{i}/{len(pending)}] OK    {source}: {words} lafz")

    # ---- 3. CSV index update karo --------------------------------
    is_new = not os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if is_new:
            w.writerow(HEADERS)
            print(f"\n==> Nayi CSV bana di: {CSV_FILE}")
        w.writerows(new_rows)

    # ---- 4. Aaj ka digest ----------------------------------------
    digest_path = os.path.join(DIGEST_DIR, f"{today}.md")
    by_source = {}
    for row in new_rows:
        by_source.setdefault(row[1], []).append(row)

    exists = os.path.exists(digest_path)
    with open(digest_path, "a", encoding="utf-8") as f:
        if not exists:
            f.write(f"# Khabrein - {today}\n")
        f.write(f"\n_Jama kiya gaya: {stamp}_\n")
        for name, rows in by_source.items():
            f.write(f"\n## {name}\n\n")
            for _, _, _, title, link, words, path in rows:
                if path:
                    local = os.path.relpath(path, DIGEST_DIR).replace("\\", "/")
                    f.write(f"- [{title}]({link}) - [poora matn]({local}) ({words} lafz)\n")
                else:
                    f.write(f"- [{title}]({link}) - _matn nahi mila_\n")

    # ---- 5. Khulasa ----------------------------------------------
    total_words = sum(r[5] for r in new_rows)
    bar = "=" * 46
    print(f"\n{bar}")
    print(f"  Nayi khabrein      : {len(new_rows)}")
    print(f"  Content mil gaya   : {len(new_rows) - no_content}")
    print(f"  Content nahi mila  : {no_content}")
    print(f"  Kul lafz           : {total_words:,}")
    print(f"  Articles yahan     : {day_dir}/")
    print(f"  Digest             : {digest_path}")
    if failures:
        print(f"  Nakam feeds        : {', '.join(failures)}")
    print(bar)

    return 0


if __name__ == "__main__":
    sys.exit(main())

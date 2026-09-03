"""
GRAFEIO Lead Crawler — Iskanje e-maila "drugje na spletu"
============================================================
Za HOT/golden leade, ki NIMAJO lastne spletne strani (torej jim
diagnose.py/backfill_emails.py ne more pomagati), poskusi najti
e-mail prek splosnega spletnega iskanja (DuckDuckGo HTML, brez
potrebnega API kljuca) — npr. Facebook/Instagram stran, imenik,
PR objava ipd.

To je "best effort": za majhno lokalno podjetje brez spletne strani
e-mail pogosto sploh ni javno objavljen nikjer. Pricakuj nizko
stopnjo uspesnosti (morda 5-15%). Rezultat NE prepise obstojecih
podatkov — shrani se v locen CSV za pregled, preden se zdruzi.

Uporaba:
    python3 search_web_emails.py <leads.json> [--limit N]
"""

import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import quote_plus

import requests
from bs4 import BeautifulSoup

from diagnose import EMAIL_REGEX, _is_junk_email, HEADERS as SITE_HEADERS
from config import OUTPUT_DIR

MAX_WORKERS = 4
SEARCH_TIMEOUT = 8
DELAY_BETWEEN = 0.3  # dodatna vljudnost do DuckDuckGo

SEARCH_HEADERS = dict(SITE_HEADERS)
SEARCH_HEADERS["Accept-Language"] = "sl-SI,sl;q=0.9,en;q=0.8"


def ddg_search(query, max_results=5):
    """Vrne seznam (naslov, url, snippet) iz DuckDuckGo HTML iskanja."""
    url = "https://html.duckduckgo.com/html/"
    try:
        resp = requests.post(
            url, data={"q": query}, headers=SEARCH_HEADERS, timeout=SEARCH_TIMEOUT
        )
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        results = []
        for res in soup.select(".result")[:max_results]:
            a = res.select_one(".result__a")
            snippet_el = res.select_one(".result__snippet")
            if not a:
                continue
            title = a.get_text(strip=True)
            href = a.get("href", "")
            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""
            results.append((title, href, snippet))
        return results
    except Exception:
        return []


def emails_from_text(text):
    found = EMAIL_REGEX.findall(text)
    clean = []
    seen = set()
    for e in found:
        e = e.strip().strip(".,;:").lower()
        if not e or e in seen or _is_junk_email(e):
            continue
        seen.add(e)
        clean.append(e)
    return clean


def try_fetch_page_emails(url):
    """Obisci stran (npr. Facebook/imenik zadetek) in poisci e-mail v besedilu."""
    try:
        resp = requests.get(url, headers=SITE_HEADERS, timeout=SEARCH_TIMEOUT)
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, "lxml")
        return emails_from_text(soup.get_text(" ", strip=True))
    except Exception:
        return []


def find_email_for_lead(lead):
    """Poskusi najti e-mail za en lead prek spletnega iskanja."""
    name = lead.get("name", "").strip()
    location = lead.get("location", "").strip()
    if not name:
        return "", "", ""

    query = f'"{name}" {location} email OR e-mail OR kontakt'
    results = ddg_search(query)

    # 1. Poisci e-mail neposredno v naslovih/snippetih rezultatov
    for title, href, snippet in results:
        emails = emails_from_text(title + " " + snippet)
        if emails:
            return emails[0], href, "iskanje (snippet)"

    # 2. Ce ne, obisci prvi obetaven rezultat (drugo kot bizi/pisi/znano imeniski spam)
    for title, href, snippet in results[:3]:
        if not href.startswith("http"):
            continue
        emails = try_fetch_page_emails(href)
        if emails:
            return emails[0], href, "iskanje (stran)"

    return "", "", ""


def load_leads_json(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    if len(sys.argv) < 2:
        print("Uporaba: python3 search_web_emails.py <leads.json> [--limit N]")
        sys.exit(1)

    filepath = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    data = load_leads_json(filepath)
    leads = data.get("leads", [])

    targets = [
        l for l in leads
        if (l.get("classification") == "HOT" or l.get("golden_lead") == "DA")
        and not (l.get("email") or "").strip()
    ]
    if limit:
        targets = targets[:limit]

    print(f"HOT/golden leadi brez e-maila: {len(targets)}")
    print(f"Vzporednih delavcev: {MAX_WORKERS}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = os.path.join(OUTPUT_DIR, "web_search_emails.csv")

    results = []
    start = time.time()
    done = 0
    found_count = 0

    def worker(lead):
        time.sleep(DELAY_BETWEEN)
        email, source_url, method = find_email_for_lead(lead)
        return lead, email, source_url, method

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(worker, l) for l in targets]
        for fut in as_completed(futures):
            lead, email, source_url, method = fut.result()
            results.append({
                "place_id": lead.get("place_id", ""),
                "name": lead.get("name", ""),
                "address": lead.get("address", ""),
                "location": lead.get("location", ""),
                "web_email": email,
                "web_email_source_url": source_url,
                "web_email_method": method,
            })
            if email:
                found_count += 1
            done += 1
            if done % 50 == 0 or done == len(targets):
                elapsed = time.time() - start
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (len(targets) - done) / rate if rate > 0 else 0
                print(
                    f"  [{done}/{len(targets)}] najdenih: {found_count} "
                    f"({elapsed:.0f}s, ~{remaining:.0f}s do konca)"
                )

    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["place_id", "name", "address", "location",
                      "web_email", "web_email_source_url", "web_email_method"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n=== KONČANO ===")
    print(f"Najdenih e-mailov: {found_count} / {len(targets)}")
    print(f"Shranjeno v {out_path} (za pregled pred zdruzitvijo v leads.json)")


if __name__ == "__main__":
    main()

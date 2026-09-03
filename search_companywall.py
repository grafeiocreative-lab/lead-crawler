"""
GRAFEIO Lead Crawler — E-mail prek companywall.si
====================================================
Za HOT/golden leade brez e-maila (in brez lastne strani) poisce
podjetje na companywall.si (javni imenik, izpeljan iz AJPES/PRS
podatkov) in iz profila podjetja izlusci e-mail, ce je objavljen
(companywall.si prikazuje registriran e-mail v navadnem besedilu,
ne za bizi.si placljivim orodjem).

Za razliko od search_web_emails.py (DuckDuckGo) ta skript kliče
navadno domeno prek 'requests', kar v tem okolju DELUJE (isto kot
diagnose.py za posamezna podjetja) - zato lahko tece samostojno,
brez WebSearch orodja, na celotnem preostanku leadov.

Uporaba:
    python3 search_companywall.py <leads.json> [--limit N]
"""

import csv
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from diagnose import EMAIL_REGEX, _is_junk_email, HEADERS as SITE_HEADERS
from config import OUTPUT_DIR

MAX_WORKERS = 10
REQ_TIMEOUT = 10
COMPANYWALL_JUNK_DOMAINS = {"companywall.si"}

SEARCH_HEADERS = dict(SITE_HEADERS)
SEARCH_HEADERS["Accept-Language"] = "sl-SI,sl;q=0.9,en;q=0.8"


def emails_from_text(text):
    found = EMAIL_REGEX.findall(text)
    clean = []
    seen = set()
    for e in found:
        e = e.strip().strip(".,;:").lower()
        if not e or e in seen or _is_junk_email(e):
            continue
        if e.partition("@")[2] in COMPANYWALL_JUNK_DOMAINS:
            continue
        seen.add(e)
        clean.append(e)
    return clean


def find_profile_url(name):
    """Poisce profil podjetja na companywall.si prek iskalnika."""
    try:
        resp = requests.get(
            "https://www.companywall.si/iskanje",
            params={"q": name},
            headers=SEARCH_HEADERS,
            timeout=REQ_TIMEOUT,
        )
        if resp.status_code != 200:
            return None
        soup = BeautifulSoup(resp.text, "lxml")
        links = [
            a["href"] for a in soup.find_all("a", href=True)
            if "/podjetje/" in a["href"]
        ]
        if not links:
            return None
        href = links[0]
        if href.startswith("/"):
            href = "https://www.companywall.si" + href
        return href
    except Exception:
        return None


def find_email_for_lead(lead):
    name = (lead.get("name") or "").strip()
    if not name:
        return "", ""

    profile_url = find_profile_url(name)
    if not profile_url:
        return "", ""

    try:
        resp = requests.get(profile_url, headers=SITE_HEADERS, timeout=REQ_TIMEOUT)
        if resp.status_code != 200:
            return "", ""
        soup = BeautifulSoup(resp.text, "lxml")
        emails = emails_from_text(soup.get_text(" ", strip=True))
        if emails:
            return emails[0], profile_url
    except Exception:
        pass

    return "", ""


def main():
    if len(sys.argv) < 2:
        print("Uporaba: python3 search_companywall.py <leads.json> [--limit N]")
        sys.exit(1)

    filepath = sys.argv[1]
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])

    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
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
    out_path = os.path.join(OUTPUT_DIR, "companywall_emails.csv")

    results = []
    start = time.time()
    done = 0
    found_count = 0

    def worker(lead):
        email, source_url = find_email_for_lead(lead)
        return lead, email, source_url

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = [ex.submit(worker, l) for l in targets]
        for fut in as_completed(futures):
            lead, email, source_url = fut.result()
            results.append({
                "place_id": lead.get("place_id", ""),
                "name": lead.get("name", ""),
                "address": lead.get("address", ""),
                "location": lead.get("location", ""),
                "web_email": email,
                "web_email_source_url": source_url,
                "web_email_method": "companywall" if email else "",
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

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        fieldnames = ["place_id", "name", "address", "location",
                      "web_email", "web_email_source_url", "web_email_method"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n=== KONČANO ===")
    print(f"Najdenih e-mailov: {found_count} / {len(targets)}")
    print(f"Shranjeno v {out_path}")


if __name__ == "__main__":
    main()

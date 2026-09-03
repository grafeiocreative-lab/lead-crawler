"""
GRAFEIO Lead Crawler — Backfill e-mail naslovov
==================================================
Enkratni skript: doda "email"/"email_source" stolpca k ze obstojecim
leadom (leads_enriched.csv), ne da bi bilo treba znova pognati celoten
pocasen diagnose.py pipeline. Uporablja isto logiko zajema (mailto:
linki + regex + kontakt stran) kot diagnose.py, samo vzporedno (hitreje).

Uporaba:
    python3 backfill_emails.py output/leads_enriched.csv
"""

import csv
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from bs4 import BeautifulSoup

from diagnose import HEADERS, extract_emails, find_contact_page_url
from config import HTTP_TIMEOUT, OUTPUT_DIR

MAX_WORKERS = 15


def fetch_email_for(row):
    """Vrne (row_index_key, email, email_source) za eno podjetje."""
    website = (row.get("website") or "").strip()
    if not website:
        return "", ""

    url = website if website.startswith("http") else "https://" + website

    try:
        resp = requests.get(url, headers=HEADERS, timeout=HTTP_TIMEOUT, allow_redirects=True)
        if resp.status_code >= 400:
            return "", ""
        soup = BeautifulSoup(resp.text, "lxml")

        emails = extract_emails(soup)
        if emails:
            return "; ".join(emails[:3]), "naslovnica"

        contact_url = find_contact_page_url(soup, resp.url)
        if contact_url:
            c_resp = requests.get(contact_url, headers=HEADERS, timeout=HTTP_TIMEOUT)
            if c_resp.status_code == 200:
                c_soup = BeautifulSoup(c_resp.text, "lxml")
                c_emails = extract_emails(c_soup)
                if c_emails:
                    return "; ".join(c_emails[:3]), "kontakt stran"
    except Exception:
        pass

    return "", ""


def load_csv(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader), reader.fieldnames


def main():
    if len(sys.argv) < 2:
        print("Uporaba: python3 backfill_emails.py <leads_enriched.csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    rows, fieldnames = load_csv(filepath)

    if "email" not in fieldnames:
        fieldnames = list(fieldnames) + ["email", "email_source"]
    if "email_source" not in fieldnames:
        fieldnames = list(fieldnames) + ["email_source"]

    to_process = [
        (i, row) for i, row in enumerate(rows)
        if (row.get("website") or "").strip() and not (row.get("email") or "").strip()
    ]

    print(f"Skupaj vrstic: {len(rows)}")
    print(f"S stranjo, brez e-maila (za obdelavo): {len(to_process)}")
    print(f"Vzporednih delavcev: {MAX_WORKERS}\n")

    start = time.time()
    done = 0
    found_count = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as ex:
        futures = {ex.submit(fetch_email_for, row): i for i, row in to_process}
        for fut in as_completed(futures):
            i = futures[fut]
            email, source = fut.result()
            rows[i]["email"] = email
            rows[i]["email_source"] = source
            if email:
                found_count += 1
            done += 1
            if done % 200 == 0 or done == len(to_process):
                elapsed = time.time() - start
                rate = done / elapsed if elapsed > 0 else 0
                remaining = (len(to_process) - done) / rate if rate > 0 else 0
                print(
                    f"  [{done}/{len(to_process)}] najdenih e-mailov: {found_count} "
                    f"({elapsed:.0f}s, ~{remaining:.0f}s do konca)"
                )

    # Za vrstice brez website-a, ki nimajo se teh polj
    for row in rows:
        row.setdefault("email", "")
        row.setdefault("email_source", "")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out_path = filepath
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total_with_email = sum(1 for r in rows if (r.get("email") or "").strip())
    print(f"\n=== KONČANO ===")
    print(f"Skupaj leadov z e-mailom: {total_with_email}")
    print(f"Shranjeno v {out_path}")


if __name__ == "__main__":
    main()

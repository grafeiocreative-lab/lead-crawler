#!/usr/bin/env python3
"""
GRAFEIO Lead Crawler — Glavni program
=======================================

Uporaba:
    python main.py all              # Celoten pipeline: zberi + diagnostika + scoring
    python main.py collect           # Samo zbiranje (Maps + bizi.si)
    python main.py collect-maps      # Samo Google Maps
    python main.py collect-bizi      # Samo bizi.si
    python main.py diagnose          # Diagnostika (potrebuje businesses CSV)
    python main.py score             # Scoring (potrebuje diagnostics CSV)
    python main.py quick <url>       # Hitra diagnostika ene strani
"""

import csv
import os
import sys
from datetime import datetime

from config import OUTPUT_DIR


def merge_csvs(files, output_filename="businesses_all.csv"):
    """Zdruzni vec CSV datotek v eno."""
    all_rows = []
    all_fields = set()

    for filepath in files:
        if not filepath or not os.path.exists(filepath):
            continue
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                all_fields.update(row.keys())
                all_rows.append(row)

    if not all_rows:
        return None

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, output_filename)

    # Deduplikacija po imenu
    seen = set()
    unique = []
    for row in all_rows:
        key = row.get("name", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(row)

    fieldnames = list(unique[0].keys()) if unique else list(all_fields)
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n  Zdruzeno {len(unique)} podjetij (deduplicirano) v {filepath}")
    return filepath


def cmd_collect_maps():
    """Zberi podjetja iz Google Maps."""
    from collect_maps import collect_from_maps, save_businesses

    print("\n=== 1/3 Google Maps zbiralnik ===\n")
    businesses = collect_from_maps()
    if businesses:
        return save_businesses(businesses)
    return None


def cmd_collect_bizi():
    """Zberi podjetja iz bizi.si."""
    from collect_bizi import collect_from_bizi, save_businesses

    print("\n=== 2/3 bizi.si zbiralnik ===\n")
    businesses = collect_from_bizi()
    if businesses:
        return save_businesses(businesses)
    return None


def cmd_diagnose(input_file=None):
    """Izvedi diagnostiko."""
    from diagnose import load_businesses, run_diagnostics, save_diagnostics

    if not input_file:
        input_file = os.path.join(OUTPUT_DIR, "businesses_all.csv")

    if not os.path.exists(input_file):
        print(f"NAPAKA: datoteka {input_file} ne obstaja.")
        print("Najprej pozeni: python main.py collect")
        return None

    print(f"\n=== Diagnostika spletnih strani ===\n")
    print(f"Vhod: {input_file}")
    businesses = load_businesses(input_file)
    results = run_diagnostics(businesses)
    return save_diagnostics(results)


def cmd_score(input_file=None):
    """Izvedi scoring."""
    from score import load_diagnostics, run_scoring, save_scored

    if not input_file:
        input_file = os.path.join(OUTPUT_DIR, "diagnostics.csv")

    if not os.path.exists(input_file):
        print(f"NAPAKA: datoteka {input_file} ne obstaja.")
        print("Najprej pozeni: python main.py diagnose")
        return None

    print(f"\n=== Lead scoring ===\n")
    print(f"Vhod: {input_file}")
    diagnostics = load_diagnostics(input_file)
    scored = run_scoring(diagnostics)
    return save_scored(scored)


def cmd_quick(url):
    """Hitra diagnostika ene spletne strani."""
    from diagnose import diagnose_website
    from score import score_lead, classify_lead

    print(f"\n=== Hitra diagnostika: {url} ===\n")

    diag = diagnose_website(url)
    diag["has_website"] = True

    score, reasons = score_lead(diag)
    classification = classify_lead(score)

    print(f"  Stran:          {diag['url']}")
    print(f"  Dosegljiva:     {'DA' if diag['reachable'] else 'NE'}")
    print(f"  Status:         {diag['status_code']}")
    print(f"  Nalaganje:      {diag['load_time_s']}s")
    print(f"  SSL:            {'DA' if diag['has_ssl'] else 'NE'}")
    print(f"  Mobilna:        {'DA' if diag['is_mobile_friendly'] else 'NE'}")
    print(f"  Title:          {diag['title'][:60] if diag['title'] else 'NI'}")
    print(f"  Meta opis:      {'DA' if diag['has_meta_description'] else 'NE'}")
    print(f"  H1:             {'DA' if diag['has_h1'] else 'NE'}")
    print(f"  Favicon:        {'DA' if diag['has_favicon'] else 'NE'}")
    print(f"  Copyright:      {diag['copyright_year'] or 'ni najden'}")
    print(f"  Slike brez alt: {diag['images_without_alt']}/{diag['images_total']}")
    print(f"  Social linki:   {diag['social_count']}")
    print(f"  Broken linki:   {diag['broken_links_count']}")
    print(f"  robots.txt:     {'DA' if diag['has_robots'] else 'NE'}")
    print(f"  sitemap.xml:    {'DA' if diag['has_sitemap'] else 'NE'}")
    print(f"  CMS:            {diag['generator'] or 'ni zaznan'}")

    print(f"\n  --- LEAD OCENA ---")
    print(f"  Score:          {score}")
    print(f"  Klasifikacija:  {classification}")
    print(f"  Razlogi:        {'; '.join(reasons) if reasons else 'brez opomb'}")


def cmd_all():
    """Celoten pipeline."""
    print("=" * 60)
    print(f"  GRAFEIO Lead Crawler")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. Zbiranje
    maps_file = cmd_collect_maps()
    bizi_file = cmd_collect_bizi()

    # 2. Zdruzi
    merged_file = merge_csvs(
        [f for f in [maps_file, bizi_file] if f],
        "businesses_all.csv",
    )

    if not merged_file:
        print("\nNAPAKA: ni podjetij za analizo.")
        return

    # 3. Diagnostika
    diag_file = cmd_diagnose(merged_file)

    # 4. Scoring
    if diag_file:
        cmd_score(diag_file)

    print("\n" + "=" * 60)
    print("  Koncano. Rezultati v mapi: output/")
    print("  Odpri leads_scored.csv za pregled.")
    print("=" * 60)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    cmd = sys.argv[1].lower()

    if cmd == "all":
        cmd_all()
    elif cmd == "collect":
        maps_file = cmd_collect_maps()
        bizi_file = cmd_collect_bizi()
        merge_csvs([f for f in [maps_file, bizi_file] if f])
    elif cmd == "collect-maps":
        cmd_collect_maps()
    elif cmd == "collect-bizi":
        cmd_collect_bizi()
    elif cmd == "diagnose":
        input_file = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_diagnose(input_file)
    elif cmd == "score":
        input_file = sys.argv[2] if len(sys.argv) > 2 else None
        cmd_score(input_file)
    elif cmd == "quick":
        if len(sys.argv) < 3:
            print("Uporaba: python main.py quick <url>")
            sys.exit(1)
        cmd_quick(sys.argv[2])
    else:
        print(f"Neznan ukaz: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()

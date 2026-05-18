"""
GRAFEIO Lead Crawler — Obogatitev leadov
==========================================
Modul za obogatitev obstojecih leadov z dodatnimi signali:

1. Google Reviews Score (GRS) — ponderiran signal iz ocene in stevila recenzij
2. GBP brez spletne strani — oznaci podjetja z Google profilom, a brez websiteUri
3. Konkurencni pregled — po lokaciji in panogi
4. Lead prioriteta — kombiniran signal za Barbaro

Uporaba:
    python enrich.py output/leads_scored.csv
    python enrich.py output/leads_scored.csv --report
"""

import csv
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

OUTPUT_DIR = "output"


# ============================================================
# 1. GOOGLE REVIEWS SCORE (GRS)
# ============================================================

def calculate_grs(rating, reviews_count):
    """Izracunaj Google Reviews Score.

    GRS uposteva:
    - rating (1-5): kvaliteta storitve
    - reviews_count: koliko strank je ocenilo
    - Bayesian average: izogni se precenjevanju podjetij z malo ocenami

    Vrnjena vrednost: 0-100
    Visji GRS = bolj uveljavljen, a potencialno tudi bolj zadovoljen s statusom quo.

    Za lead generation nas zanima OBRATNO:
    - Visok GRS + brez spletne strani = ZLATO (imajo promet, nimajo kanala)
    - Nizek GRS + brez spletne strani = manj zanimivo (nimajo niti prometa)
    """
    try:
        rating = float(rating) if rating else 0
        reviews_count = int(float(reviews_count)) if reviews_count else 0
    except (ValueError, TypeError):
        return 0

    if rating == 0 or reviews_count == 0:
        return 0

    # Bayesian average: utezi proti povprecju (3.5) za podjetja z malo ocenami
    # C = minimalna utez (10 recenzij preden zaupamo oceni)
    C = 10
    m = 3.5  # prior (povprecno pricakovano)
    bayesian_rating = (reviews_count * rating + C * m) / (reviews_count + C)

    # Normaliziraj na 0-100
    # bayesian_rating je med 1-5, preslikaj na 0-100
    rating_score = (bayesian_rating - 1) / 4 * 60  # max 60 tock iz ocene

    # Dodaj bonus za stevilo recenzij (logaritmicno)
    import math
    volume_score = min(40, math.log10(max(1, reviews_count)) * 20)  # max 40 tock

    return round(rating_score + volume_score, 1)


def classify_grs(grs):
    """Kategoriziraj GRS nivo."""
    if grs >= 70:
        return "UVELJAVLJEN"     # mocno podjetje, veliko ocen
    elif grs >= 40:
        return "AKTIVEN"         # solidno podjetje
    elif grs > 0:
        return "ZAČETNIK"        # malo ocen ali nizka ocena
    else:
        return "BREZ_PROFILA"    # ni na Google Maps ali ni ocen


# ============================================================
# 2. LEAD SIGNAL FLAGS
# ============================================================

def compute_lead_flags(lead):
    """Dodaj boolean signalne zastavice leadu."""
    website = str(lead.get("website", "")).strip()
    rating = lead.get("rating", "") or lead.get("google_rating", "")
    reviews = lead.get("reviews_count", "") or lead.get("google_reviews_count", "")

    has_website = bool(website) and website.lower() not in ("", "nan", "none")
    has_gbp = bool(lead.get("place_id", "")) or bool(lead.get("name", ""))

    try:
        rating_val = float(rating) if rating else 0
    except (ValueError, TypeError):
        rating_val = 0

    try:
        reviews_val = int(float(reviews)) if reviews else 0
    except (ValueError, TypeError):
        reviews_val = 0

    return {
        "has_website": has_website,
        "has_gbp": has_gbp,
        "gbp_no_website": has_gbp and not has_website,
        "high_rating": rating_val >= 4.5,
        "many_reviews": reviews_val >= 30,
        "few_reviews": 0 < reviews_val < 10,
        "no_reviews": reviews_val == 0 and has_gbp,
        "golden_lead": (
            not has_website
            and rating_val >= 4.0
            and reviews_val >= 20
        ),
    }


# ============================================================
# 3. KONKURENČNI PREGLED
# ============================================================

def build_competitive_report(leads):
    """Zgradi konkurencni pregled po lokaciji in panogi.

    Vrne dict z lokacijami, za vsako:
    - stevilo podjetij
    - koliko ima spletno stran
    - koliko ima Google Ads (ne moremo zaznati, ampak pustimo placeholder)
    - povprecna ocena
    - top 3 po ocenah
    """
    # Grupiraj po lokaciji (izloci mesto iz naslova)
    by_location = defaultdict(list)
    by_category = defaultdict(list)

    for lead in leads:
        # Poskusi izlusiti mesto iz naslova
        address = lead.get("address", "")
        city = extract_city(address)
        if city:
            by_location[city].append(lead)

        # Kategorija iz source query ali types
        category = lead.get("search_query", "") or lead.get("types", "")
        if category:
            # Poenostavi: vzemi prvo besedo
            cat_key = category.split(",")[0].strip().split(" ")[0].lower()
            by_category[cat_key].append(lead)

    report = {
        "generated": datetime.now().isoformat(),
        "total_leads": len(leads),
        "locations": {},
        "categories": {},
    }

    for city, city_leads in sorted(by_location.items()):
        stats = compute_group_stats(city_leads)
        report["locations"][city] = stats

    for cat, cat_leads in sorted(by_category.items()):
        if len(cat_leads) >= 2:  # samo ce je vec kot 1
            stats = compute_group_stats(cat_leads)
            report["categories"][cat] = stats

    return report


def compute_group_stats(leads):
    """Izracunaj statistike za skupino leadov."""
    total = len(leads)
    with_website = sum(
        1 for l in leads
        if str(l.get("website", "")).strip()
        and str(l.get("website", "")).lower() not in ("", "nan", "none")
    )
    without_website = total - with_website

    ratings = []
    for l in leads:
        try:
            r = float(l.get("rating", 0) or l.get("google_rating", 0) or 0)
            if r > 0:
                ratings.append(r)
        except (ValueError, TypeError):
            pass

    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0

    # Top 3 po ocenah
    rated_leads = []
    for l in leads:
        try:
            r = float(l.get("rating", 0) or l.get("google_rating", 0) or 0)
            rc = int(float(l.get("reviews_count", 0) or l.get("google_reviews_count", 0) or 0))
            rated_leads.append((l.get("name", ""), r, rc))
        except (ValueError, TypeError):
            pass

    top3 = sorted(rated_leads, key=lambda x: (-x[1], -x[2]))[:3]

    return {
        "skupaj": total,
        "s_spletno_stranjo": with_website,
        "brez_spletne_strani": without_website,
        "delež_brez_strani_%": round(without_website / total * 100, 1) if total > 0 else 0,
        "povprecna_ocena": avg_rating,
        "stevilo_z_oceno": len(ratings),
        "top_3": [
            {"ime": name, "ocena": r, "recenzij": rc}
            for name, r, rc in top3
        ],
    }


def extract_city(address):
    """Izloci mesto iz slovenskega naslova.

    Tipicen format: "Ulica 123, 2000 Maribor, Slovenija"
    """
    if not address:
        return ""

    parts = address.split(",")
    for part in parts:
        part = part.strip()
        # Isci vzorec: 4-mestna stevilka + ime
        words = part.split()
        if len(words) >= 2:
            # Preveri ali je prva beseda poštna stevilka
            if words[0].isdigit() and len(words[0]) == 4:
                return " ".join(words[1:])

    # Fallback: zadnji del pred "Slovenija"
    for part in reversed(parts):
        part = part.strip()
        if part.lower() not in ("slovenija", "slovenia", "si"):
            return part

    return ""


# ============================================================
# 4. ENRICH PIPELINE
# ============================================================

def enrich_leads(leads):
    """Obogati seznam leadov z GRS, zastavicami in prioriteto."""
    enriched = []

    for lead in leads:
        rating = lead.get("rating", "") or lead.get("google_rating", "")
        reviews = lead.get("reviews_count", "") or lead.get("google_reviews_count", "")

        # Google Reviews Score
        grs = calculate_grs(rating, reviews)
        grs_level = classify_grs(grs)

        # Signalne zastavice
        flags = compute_lead_flags(lead)

        # Prioritetni signal za Barbaro
        priority = compute_priority(lead, grs, flags)

        enriched_lead = dict(lead)
        enriched_lead.update({
            "grs": grs,
            "grs_level": grs_level,
            "gbp_no_website": "DA" if flags["gbp_no_website"] else "NE",
            "golden_lead": "DA" if flags["golden_lead"] else "NE",
            "high_rating": "DA" if flags["high_rating"] else "NE",
            "many_reviews": "DA" if flags["many_reviews"] else "NE",
            "priority": priority,
            "enriched_at": datetime.now().strftime("%Y-%m-%d"),
        })

        enriched.append(enriched_lead)

    # Sortiraj: golden leadi najprej, potem po prioriteti
    enriched.sort(key=lambda x: (
        x["golden_lead"] != "DA",
        -x.get("priority", 0),
    ))

    return enriched


def compute_priority(lead, grs, flags):
    """Izracunaj prioriteto leada (0-100).

    Visja prioriteta = bolj zanimiv za Barbaro.

    Logika:
    - Brez spletne strani: +40
    - GBP profil brez strani: +15 (pokazatelj da so aktivni)
    - Visoka ocena: +10
    - Veliko recenzij: +15 (dokazano povpraševanje)
    - Golden lead bonus: +20
    - Obstoječi classification HOT: +10 (iz score.py)
    """
    priority = 0

    website = str(lead.get("website", "")).strip()
    has_website = bool(website) and website.lower() not in ("", "nan", "none")

    if not has_website:
        priority += 40

    if flags.get("gbp_no_website"):
        priority += 15

    if flags.get("high_rating"):
        priority += 10

    if flags.get("many_reviews"):
        priority += 15

    if flags.get("golden_lead"):
        priority += 20

    # Bonus iz obstojecega scoringa
    classification = lead.get("classification", "")
    if classification == "HOT":
        priority += 10
    elif classification == "WARM":
        priority += 5

    return min(100, priority)


# ============================================================
# 5. SHRANJEVANJE
# ============================================================

def save_enriched(enriched, filename="leads_enriched.csv"):
    """Shrani obogatene leade v CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not enriched:
        print("Ni rezultatov za shranjevanje.")
        return None

    fieldnames = enriched[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(enriched)

    # Statistika
    golden = sum(1 for e in enriched if e["golden_lead"] == "DA")
    gbp_no_web = sum(1 for e in enriched if e["gbp_no_website"] == "DA")
    high_prio = sum(1 for e in enriched if e.get("priority", 0) >= 70)

    print(f"\n  === OBOGATITEV KONČANA ===")
    print(f"  Skupaj leadov:          {len(enriched)}")
    print(f"  Golden leadi:           {golden}")
    print(f"  GBP brez strani:        {gbp_no_web}")
    print(f"  Visoka prioriteta (70+): {high_prio}")
    print(f"  Shranjeno v {filepath}")

    return filepath


def save_competitive_report(report, filename="competitive_report.json"):
    """Shrani konkurencni pregled v JSON."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    loc_count = len(report.get("locations", {}))
    cat_count = len(report.get("categories", {}))

    print(f"\n  === KONKURENČNI PREGLED ===")
    print(f"  Lokacij: {loc_count}")
    print(f"  Kategorij: {cat_count}")
    print(f"  Shranjeno v {filepath}")

    return filepath


def save_competitive_report_txt(report, filename="competitive_report.txt"):
    """Shrani konkurencni pregled kot berljiv TXT (za Barbaro)."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    lines = []
    lines.append("=" * 60)
    lines.append("GRAFEIO · Konkurenčni pregled")
    lines.append(f"Generirano: {report.get('generated', '')[:10]}")
    lines.append(f"Skupaj analiziranih podjetij: {report.get('total_leads', 0)}")
    lines.append("=" * 60)

    # Po lokacijah
    locations = report.get("locations", {})
    if locations:
        lines.append("")
        lines.append("PO MESTIH")
        lines.append("-" * 40)

        for city, stats in sorted(
            locations.items(),
            key=lambda x: x[1]["brez_spletne_strani"],
            reverse=True,
        ):
            lines.append(f"\n  {city.upper()}")
            lines.append(f"    Podjetij:        {stats['skupaj']}")
            lines.append(f"    S spletno stranjo: {stats['s_spletno_stranjo']}")
            lines.append(f"    BREZ strani:     {stats['brez_spletne_strani']} ({stats['delež_brez_strani_%']}%)")
            lines.append(f"    Povp. ocena:     {stats['povprecna_ocena']}")

            if stats.get("top_3"):
                lines.append(f"    Top 3:")
                for t in stats["top_3"]:
                    lines.append(
                        f"      {t['ime']}: {t['ocena']} ({t['recenzij']} recenzij)"
                    )

    # Po kategorijah
    categories = report.get("categories", {})
    if categories:
        lines.append("")
        lines.append("")
        lines.append("PO DEJAVNOSTIH")
        lines.append("-" * 40)

        for cat, stats in sorted(
            categories.items(),
            key=lambda x: x[1]["brez_spletne_strani"],
            reverse=True,
        ):
            lines.append(f"\n  {cat.upper()}")
            lines.append(f"    Podjetij: {stats['skupaj']}, brez strani: {stats['brez_spletne_strani']}")
            lines.append(f"    Povp. ocena: {stats['povprecna_ocena']}")

    lines.append("")
    lines.append("=" * 60)
    lines.append("GRAFEIO · Gradnik odličnosti · grafeio.si")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"  TXT verzija v {filepath}")
    return filepath


# ============================================================
# 6. CLI
# ============================================================

def load_csv(filepath):
    """Nalozi CSV v seznam dictov."""
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(dict(row))
    return results


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uporaba:")
        print("  python enrich.py <leads.csv>            # obogati leade")
        print("  python enrich.py <leads.csv> --report    # + konkurenčni pregled")
        sys.exit(1)

    filepath = sys.argv[1]
    do_report = "--report" in sys.argv

    print(f"=== Obogatitev leadov ===")
    print(f"Vhod: {filepath}")

    leads = load_csv(filepath)
    print(f"Naloženih leadov: {len(leads)}")

    # Obogati
    enriched = enrich_leads(leads)
    save_enriched(enriched)

    # Konkurenčni pregled
    if do_report:
        report = build_competitive_report(enriched)
        save_competitive_report(report)
        save_competitive_report_txt(report)

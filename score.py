"""
GRAFEIO Lead Crawler — Lead scoring
=====================================
Izracuna oceno za vsak lead na podlagi diagnostike.
"""

import csv
import os
from datetime import datetime
from config import SCORING, OUTPUT_DIR


def score_lead(diag):
    """Izracuna lead score za eno podjetje. Visji = boljsi lead za Grafeio."""
    score = 0
    reasons = []

    # 1. Nima spletne strani
    if not diag.get("has_website") or diag.get("has_website") == "False":
        score += SCORING["no_website"]
        reasons.append("nima spletne strani")
        # Ce nima strani, ostali web-checki niso relevantni
        # Ampak preverimo se Google podatke
        score += _add_google_scores(diag, reasons)
        return score, reasons

    # 2. Stran ni dosegljiva
    reachable = diag.get("reachable")
    if reachable in (False, "False", ""):
        score += SCORING["no_website"]  # Enako kot nima
        reasons.append("stran ni dosegljiva")
        score += _add_google_scores(diag, reasons)
        return score, reasons

    # 3. SSL
    if diag.get("has_ssl") in (False, "False", ""):
        score += SCORING["no_ssl"]
        reasons.append("ni SSL certifikata")

    # 4. Mobile
    if diag.get("is_mobile_friendly") in (False, "False", ""):
        score += SCORING["not_mobile"]
        reasons.append("ni mobilno prilagojena")

    # 5. Pocasno nalaganje
    load_time = diag.get("load_time_s")
    if load_time:
        try:
            if float(load_time) > 5.0:
                score += SCORING["slow_load"]
                reasons.append(f"pocasno nalaganje ({load_time}s)")
        except ValueError:
            pass

    # 6. Meta description
    if diag.get("has_meta_description") in (False, "False", ""):
        score += SCORING["no_meta_description"]
        reasons.append("ni meta opisa")

    # 7. Title
    if diag.get("has_title") in (False, "False", ""):
        score += SCORING["no_title"]
        reasons.append("ni naslova strani")

    # 8. Copyright leto
    copyright_year = diag.get("copyright_year")
    if copyright_year:
        try:
            year = int(copyright_year)
            current_year = datetime.now().year
            if current_year - year >= 2:
                score += SCORING["old_copyright"]
                reasons.append(f"copyright {year}")
        except ValueError:
            pass
    else:
        # Ni copyright oznake sploh
        pass

    # 9. Favicon
    if diag.get("has_favicon") in (False, "False", ""):
        score += SCORING["no_favicon"]
        reasons.append("ni favicona")

    # 10. Socialni linki
    social_count = diag.get("social_count", 0)
    try:
        if int(social_count) == 0:
            score += SCORING["no_social"]
            reasons.append("ni socialnih linkov")
    except ValueError:
        pass

    # 11. Broken links
    broken = diag.get("broken_links_count", 0)
    try:
        if int(broken) > 0:
            score += SCORING["broken_links"]
            reasons.append(f"{broken} broken linkov")
    except ValueError:
        pass

    # 12. Sitemap
    if diag.get("has_sitemap") in (False, "False", ""):
        score += SCORING["no_sitemap"]
        reasons.append("ni sitemap.xml")

    # 13. robots.txt
    if diag.get("has_robots") in (False, "False", ""):
        score += SCORING["no_robots"]
        reasons.append("ni robots.txt")

    # 14. H1
    if diag.get("has_h1") in (False, "False", ""):
        score += SCORING["no_h1"]
        reasons.append("ni H1 naslova")

    # 15. Slike brez alt
    images_no_alt = diag.get("images_without_alt", 0)
    try:
        if int(images_no_alt) > 2:
            score += SCORING["images_no_alt"]
            reasons.append(f"{images_no_alt} slik brez alt besedila")
    except ValueError:
        pass

    # Google podatki
    score += _add_google_scores(diag, reasons)

    return score, reasons


def _add_google_scores(diag, reasons):
    """Izracuna tocke na podlagi Google Maps podatkov. Vrne dodatne tocke."""
    extra = 0

    rating = diag.get("google_rating", "")
    if rating:
        try:
            if float(rating) < 4.0:
                extra += SCORING["low_google_rating"]
                reasons.append(f"Google ocena {rating}")
        except ValueError:
            pass

    reviews = diag.get("google_reviews_count", "")
    if reviews:
        try:
            if int(float(reviews)) < 10:
                extra += SCORING["few_google_reviews"]
                reasons.append(f"samo {reviews} Google recenzij")
        except ValueError:
            pass

    return extra


def classify_lead(score):
    """Klasificiraj lead na podlagi score-a."""
    if score >= 60:
        return "HOT"
    elif score >= 30:
        return "WARM"
    else:
        return "LOW"


def run_scoring(diagnostics):
    """Izracuna score za vse diagnostike."""
    scored = []

    for diag in diagnostics:
        score, reasons = score_lead(diag)
        classification = classify_lead(score)

        scored.append({
            "classification": classification,
            "score": score,
            "name": diag.get("name", ""),
            "category": diag.get("category", ""),
            "location": diag.get("location", ""),
            "address": diag.get("address", ""),
            "phone": diag.get("phone", ""),
            "website": diag.get("url", diag.get("website", "")),
            "has_website": diag.get("has_website", ""),
            "google_rating": diag.get("google_rating", ""),
            "google_reviews_count": diag.get("google_reviews_count", ""),
            "reasons": "; ".join(reasons),
            "reachable": diag.get("reachable", ""),
            "has_ssl": diag.get("has_ssl", ""),
            "is_mobile_friendly": diag.get("is_mobile_friendly", ""),
            "load_time_s": diag.get("load_time_s", ""),
            "copyright_year": diag.get("copyright_year", ""),
            "social_count": diag.get("social_count", ""),
            "broken_links_count": diag.get("broken_links_count", ""),
            "generator": diag.get("generator", ""),
        })

    # Sortiraj: HOT > WARM > LOW, znotraj po score padajoce
    order = {"HOT": 0, "WARM": 1, "LOW": 2}
    scored.sort(key=lambda x: (order.get(x["classification"], 3), -x["score"]))

    return scored


def save_scored(scored, filename="leads_scored.csv"):
    """Shrani scored leade v CSV in JSON."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not scored:
        print("Ni rezultatov za shranjevanje.")
        return

    fieldnames = scored[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(scored)

    # Shrani tudi JSON za dashboard
    import json
    json_path = os.path.join(OUTPUT_DIR, "leads.json")
    json_data = {
        "generated": datetime.now().isoformat(),
        "total": len(scored),
        "hot": sum(1 for s in scored if s["classification"] == "HOT"),
        "warm": sum(1 for s in scored if s["classification"] == "WARM"),
        "low": sum(1 for s in scored if s["classification"] == "LOW"),
        "leads": scored,
    }
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    # Izpis statistike
    print(f"\n  === REZULTATI ===")
    print(f"  HOT:  {json_data['hot']}")
    print(f"  WARM: {json_data['warm']}")
    print(f"  LOW:  {json_data['low']}")
    print(f"  Shranjeno v {filepath}")
    print(f"  JSON za dashboard: {json_path}")

    return filepath


def load_diagnostics(filepath):
    """Nalozi diagnostike iz CSV."""
    results = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(dict(row))
    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uporaba: python score.py <diagnostics.csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"=== Lead scoring ===")
    print(f"Vhod: {filepath}")

    diagnostics = load_diagnostics(filepath)
    scored = run_scoring(diagnostics)
    save_scored(scored)

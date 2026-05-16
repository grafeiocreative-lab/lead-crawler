#!/usr/bin/env python3
"""
GRAFEIO Lead Crawler — Varnostni predpregled
==============================================

Poženi PRED main.py all, da preveriš:
1. Ali je API ključ nastavljen
2. Koliko bo stalo
3. Koliko kategorij × lokacij
4. Ali si že poganjal ta mesec (prepreči dvojno zaračunavanje)

Uporaba:
    python3 preflight.py          # preveri vse
    python3 preflight.py --run    # preveri + poženi pipeline
"""

import os
import sys
from datetime import datetime

# Uvozi config (mora biti v isti mapi)
from config import (
    GOOGLE_MAPS_API_KEY,
    SEARCH_CATEGORIES,
    SEARCH_LOCATIONS,
    OUTPUT_DIR,
    estimate_cost,
    print_cost_estimate,
)


def check_api_key():
    """Preveri ali je API ključ nastavljen."""
    if not GOOGLE_MAPS_API_KEY:
        print("  ❌ API ključ NI nastavljen!")
        print("     Nastavi GOOGLE_MAPS_API_KEY v .env datoteki.")
        return False
    # Prikaži samo prvih 8 znakov
    masked = GOOGLE_MAPS_API_KEY[:8] + "..." + GOOGLE_MAPS_API_KEY[-4:]
    print(f"  ✅ API ključ: {masked}")
    return True


def check_last_run():
    """Preveri kdaj je bil zadnji zagon (prepreči dvojno zaračunavanje)."""
    marker_file = os.path.join(OUTPUT_DIR, ".last_run")

    if os.path.exists(marker_file):
        with open(marker_file, "r") as f:
            last_run = f.read().strip()
        try:
            last_date = datetime.fromisoformat(last_run)
            now = datetime.now()
            days_ago = (now - last_date).days

            if last_date.month == now.month and last_date.year == now.year:
                print(f"  ⚠️  Zadnji zagon: {last_run[:10]} ({days_ago} dni nazaj)")
                print(f"     Že si poganjal TA MESEC. Ponoven zagon podvoji strošek!")
                return "same_month"
            else:
                print(f"  ✅ Zadnji zagon: {last_run[:10]} ({days_ago} dni nazaj)")
                return "ok"
        except ValueError:
            pass

    print("  ✅ Prvič ta mesec (ali ni zgodovine)")
    return "ok"


def save_run_marker():
    """Shrani marker zadnjega zagona."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    marker_file = os.path.join(OUTPUT_DIR, ".last_run")
    with open(marker_file, "w") as f:
        f.write(datetime.now().isoformat())


def show_sample_queries():
    """Pokaži vzorec iskalnih poizvedb."""
    print(f"\n  === VZOREC POIZVEDB (prvih 5 × 3 lokacije) ===")
    cats = SEARCH_CATEGORIES[:5]
    locs = SEARCH_LOCATIONS[:3]
    for loc in locs:
        for cat in cats:
            print(f"    \"{cat} {loc}\"")
        print(f"    ... +{len(SEARCH_CATEGORIES) - 5} kategorij")
    print(f"    ... +{len(SEARCH_LOCATIONS) - 3} lokacij")


def preflight():
    """Izvedi vse preveritve."""
    print("=" * 50)
    print("GRAFEIO Lead Crawler · Predpregled")
    print("=" * 50)

    # 1. API ključ
    print("\n1. API ključ")
    api_ok = check_api_key()

    # 2. Stroški
    print("\n2. Stroški")
    within_budget = print_cost_estimate()

    # 3. Zadnji zagon
    print("\n3. Zgodovina zagonov")
    last_run_status = check_last_run()

    # 4. Vzorec
    show_sample_queries()

    # Povzetek
    print("\n" + "=" * 50)
    all_ok = api_ok and within_budget

    if not all_ok:
        print("❌ Preveritve NISO uspele. Popravi napake zgoraj.")
        return False

    if last_run_status == "same_month":
        print("⚠️  Pozor: ponoven zagon ta mesec!")
        print("   Nadaljuj samo če veš kaj delaš.")
    else:
        print("✅ Vse preveritve uspešne. Pripravljen za zagon.")

    return True


if __name__ == "__main__":
    ok = preflight()

    if "--run" in sys.argv and ok:
        print("\n")
        confirm = input("Poženi celoten pipeline? (da/ne): ").strip().lower()
        if confirm in ("da", "d", "yes", "y"):
            save_run_marker()
            print("\nZaganjam pipeline...\n")
            os.system("python3 main.py all")
        else:
            print("Prekinjeno.")
    elif "--run" in sys.argv:
        print("\nPipeline NI zagnan zaradi napak.")

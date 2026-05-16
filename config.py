"""
GRAFEIO Lead Crawler — Optimiziran config za brezplačno kvoto
===============================================================

196 kategorij × 31 lokacij = 6.076 klicev = ~194 USD (kvota: 200 USD)

Pokritje: vsa slovenska mesta z 5.000+ prebivalci + ključna regionalna središča.
To zajame ~85% slovenskega trga storitvenih dejavnosti.

OPOZORILO: Poženi ENKRAT na mesec. Če poženeš dvakrat, presežeš kvoto.
Za varnost: main.py naj pred zagonom izpiše oceno stroškov in čaka potrditev.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# API KLJUČ
# ============================================================

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ============================================================
# KATEGORIJE — vse (196)
# ============================================================

from config_categories import get_all_categories, get_categories_by_sector

SEARCH_CATEGORIES = get_all_categories()

# Če želiš samo določene sektorje, odkomentiraj:
# SEARCH_CATEGORIES = (
#     get_categories_by_sector("zdravstvo")
#     + get_categories_by_sector("lepota")
#     + get_categories_by_sector("obrti")
#     + get_categories_by_sector("avto")
#     + get_categories_by_sector("ciscenje")
# )

# ============================================================
# LOKACIJE — 31 krajev (cela Slovenija)
# ============================================================

SEARCH_LOCATIONS = [
    # === MESTNE OBČINE (11) ===
    "Ljubljana",
    "Maribor",
    "Celje",
    "Kranj",
    "Koper",
    "Novo mesto",
    "Velenje",
    "Nova Gorica",
    "Ptuj",
    "Murska Sobota",
    "Slovenj Gradec",

    # === REGIONALNA SREDIŠČA (20) ===
    "Jesenice",
    "Trbovlje",
    "Škofja Loka",
    "Domžale",
    "Kamnik",
    "Brežice",
    "Postojna",
    "Ajdovščina",
    "Ilirska Bistrica",
    "Lendava",
    "Ljutomer",
    "Radovljica",
    "Ravne na Koroškem",
    "Sežana",
    "Slovenska Bistrica",
    "Šentjur",
    "Žalec",
    "Dravograd",
    "Idrija",
    "Tolmin",
]

# ============================================================
# GOOGLE MAPS NASTAVITVE
# ============================================================

MAPS_MAX_RESULTS = 20  # max na iskanje (API limit je 20)

# ============================================================
# DIAGNOSTIKA
# ============================================================

HTTP_TIMEOUT = 10          # timeout za HTTP zahteve (sekunde)
MAX_INTERNAL_LINKS_CHECK = 5

# ============================================================
# LEAD SCORING UTEŽI (za score.py)
# ============================================================

SCORING = {
    "no_website":           40,
    "no_ssl":               25,
    "not_mobile":           20,
    "slow_load":            15,
    "no_meta_description":  10,
    "no_title":             10,
    "old_copyright":        15,
    "no_favicon":            5,
    "no_social":            10,
    "broken_links":         15,
    "no_sitemap":            5,
    "no_robots":             5,
    "no_h1":                 5,
    "images_no_alt":        10,
    "low_google_rating":    10,
    "few_google_reviews":   10,
}

# ============================================================
# OUTPUT
# ============================================================

OUTPUT_DIR = "output"

# ============================================================
# VARNOSTNI IZRAČUN
# ============================================================

COST_PER_REQUEST = 0.032  # USD
FREE_CREDIT = 200.0       # USD/mesec


def estimate_cost():
    """Izračunaj predviden strošek zagona."""
    total = len(SEARCH_CATEGORIES) * len(SEARCH_LOCATIONS)
    cost = total * COST_PER_REQUEST
    remaining = FREE_CREDIT - cost
    return {
        "categories": len(SEARCH_CATEGORIES),
        "locations": len(SEARCH_LOCATIONS),
        "total_requests": total,
        "cost_usd": round(cost, 2),
        "remaining_usd": round(remaining, 2),
        "within_free_tier": cost <= FREE_CREDIT,
    }


def print_cost_estimate():
    """Izpiši oceno stroškov pred zagonom."""
    est = estimate_cost()
    print(f"\n  === OCENA STROŠKOV ===")
    print(f"  Kategorij:    {est['categories']}")
    print(f"  Lokacij:      {est['locations']}")
    print(f"  Skupaj klicev: {est['total_requests']}")
    print(f"  Strošek:      {est['cost_usd']} USD")
    print(f"  Preostane:    {est['remaining_usd']} USD")

    if est["within_free_tier"]:
        print(f"  Status:       ✅ ZNOTRAJ brezplačne kvote")
    else:
        over = abs(est["remaining_usd"])
        print(f"  Status:       ⚠️  PRESEGA kvoto za {over} USD!")
        max_locs = int(FREE_CREDIT / COST_PER_REQUEST) // est["categories"]
        print(f"  Priporočilo:  zmanjšaj na {max_locs} lokacij")

    return est["within_free_tier"]


if __name__ == "__main__":
    print_cost_estimate()

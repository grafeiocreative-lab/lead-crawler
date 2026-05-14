"""
GRAFEIO Lead Crawler — bizi.si zbiralnik
=========================================
Isce podjetja na bizi.si po kategoriji/dejavnosti.

bizi.si je javni poslovni imenik slovenskih podjetij.
Podatki so javni (AJPES register).
"""

import csv
import os
import re
import time
import requests
from bs4 import BeautifulSoup
from config import SEARCH_LOCATIONS, OUTPUT_DIR

# bizi.si kategorije (SKD kode ali iskalni pojmi)
# Prilagodi glede na to, kaj vraca rezultate
BIZI_SEARCH_TERMS = [
    "zobozdravstvo",
    "fizioterapija",
    "kozmetični salon",
    "frizerski salon",
    "masažni salon",
    "manikura",
    "pedikura",
    "avtomehanična delavnica",
    "pasji salon",
]

BIZI_BASE_URL = "https://www.bizi.si"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "sl-SI,sl;q=0.9,en;q=0.8",
}


def search_bizi(term, location=""):
    """Isci podjetja na bizi.si."""
    businesses = []
    query = f"{term} {location}".strip()

    # bizi.si iskanje
    search_url = f"{BIZI_BASE_URL}/iskanje"
    params = {"q": query}

    try:
        resp = requests.get(
            search_url, params=params, headers=HEADERS, timeout=15
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Poiscemo rezultate
        # bizi.si struktura: vsak rezultat je v kartici s podatki
        # OPOMBA: HTML struktura se lahko spremeni, takrat prilagodi selectorje
        results = soup.select(".company-card, .search-result, .result-item, article")

        if not results:
            # Alternativni selectorji
            results = soup.find_all("div", class_=re.compile(r"company|result|item"))

        for item in results:
            name_el = item.find(["h2", "h3", "a"])
            name = name_el.get_text(strip=True) if name_el else ""

            if not name:
                continue

            # Naslov
            addr_el = item.find(class_=re.compile(r"address|addr|location"))
            address = addr_el.get_text(strip=True) if addr_el else ""

            # Telefon
            phone_el = item.find(class_=re.compile(r"phone|tel"))
            phone = phone_el.get_text(strip=True) if phone_el else ""

            # Spletna stran
            website = ""
            web_el = item.find("a", href=re.compile(r"https?://(?!www\.bizi)"))
            if web_el:
                website = web_el.get("href", "")

            # Link do profila na bizi.si
            profile_url = ""
            link_el = item.find("a", href=True)
            if link_el:
                href = link_el.get("href", "")
                if href.startswith("/"):
                    profile_url = f"{BIZI_BASE_URL}{href}"
                elif "bizi.si" in href:
                    profile_url = href

            businesses.append({
                "source": "bizi.si",
                "name": name,
                "address": address,
                "phone": phone,
                "website": website,
                "google_rating": "",
                "google_reviews_count": "",
                "place_id": "",
                "category": term,
                "location": location,
                "latitude": "",
                "longitude": "",
                "business_status": "",
                "bizi_profile": profile_url,
            })

        print(f"    Najdeno: {len(businesses)} rezultatov")

    except requests.RequestException as e:
        print(f"    Napaka: {e}")

    return businesses


def enrich_from_profile(business):
    """Pridobi dodatne podatke iz bizi.si profila podjetja."""
    profile_url = business.get("bizi_profile", "")
    if not profile_url:
        return business

    try:
        resp = requests.get(profile_url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Spletna stran iz profila
        if not business["website"]:
            web_link = soup.find("a", href=re.compile(r"https?://(?!.*bizi\.si)"))
            if web_link:
                business["website"] = web_link.get("href", "")

        # Telefon iz profila
        if not business["phone"]:
            phone_el = soup.find(string=re.compile(r"\+386|\d{3}\s?\d{3}\s?\d{3}"))
            if phone_el:
                business["phone"] = phone_el.strip()

        # Naslov iz profila
        if not business["address"]:
            addr_el = soup.find(class_=re.compile(r"address"))
            if addr_el:
                business["address"] = addr_el.get_text(strip=True)

    except Exception:
        pass

    return business


def collect_from_bizi():
    """Zbere podjetja iz bizi.si."""
    all_businesses = []
    seen_names = set()

    for location in SEARCH_LOCATIONS:
        for term in BIZI_SEARCH_TERMS:
            print(f"  Iscem: {term} {location}")
            results = search_bizi(term, location)

            for biz in results:
                # Preskok duplikatov po imenu
                key = biz["name"].lower().strip()
                if key in seen_names:
                    continue
                seen_names.add(key)
                all_businesses.append(biz)

            # Spoštuj rate limit
            time.sleep(1.5)

    # Opcijsko: obogati s profili (pocasneje, ampak vec podatkov)
    print(f"\n  Obogacujem podatke iz profilov ({len(all_businesses)} podjetij)...")
    for i, biz in enumerate(all_businesses):
        if biz.get("bizi_profile"):
            all_businesses[i] = enrich_from_profile(biz)
            time.sleep(1.0)

    return all_businesses


def save_businesses(businesses, filename="businesses_bizi.csv"):
    """Shrani podjetja v CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not businesses:
        print("Ni podjetij za shranjevanje.")
        return

    fieldnames = businesses[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(businesses)

    print(f"  Shranjeno {len(businesses)} podjetij v {filepath}")
    return filepath


if __name__ == "__main__":
    print("=== bizi.si zbiralnik ===")
    businesses = collect_from_bizi()
    if businesses:
        save_businesses(businesses)
    print(f"Skupaj: {len(businesses)} podjetij")

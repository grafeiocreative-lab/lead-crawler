"""
GRAFEIO Lead Crawler — Google Maps zbiralnik
=============================================
Isce podjetja po kategoriji in lokaciji prek Google Places API (New).
Uporablja Text Search endpoint.
"""

import csv
import os
import time
import requests
from config import (
    GOOGLE_MAPS_API_KEY,
    SEARCH_CATEGORIES,
    SEARCH_LOCATIONS,
    MAPS_MAX_RESULTS,
    OUTPUT_DIR,
)

PLACES_URL = "https://places.googleapis.com/v1/places:searchText"

FIELD_MASK = ",".join([
    "places.id",
    "places.displayName",
    "places.formattedAddress",
    "places.nationalPhoneNumber",
    "places.internationalPhoneNumber",
    "places.websiteUri",
    "places.rating",
    "places.userRatingCount",
    "places.location",
    "places.types",
    "places.businessStatus",
])


def search_places(query, max_results=MAPS_MAX_RESULTS):
    """Isci podjetja prek Places API (New) Text Search."""
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": GOOGLE_MAPS_API_KEY,
        "X-Goog-FieldMask": FIELD_MASK,
    }

    body = {
        "textQuery": query,
        "languageCode": "sl",
        "maxResultCount": min(max_results, 20),
    }

    all_places = []

    try:
        resp = requests.post(PLACES_URL, json=body, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        for place in data.get("places", []):
            loc = place.get("location", {})
            name = place.get("displayName", {})

            all_places.append({
                "place_id": place.get("id", ""),
                "name": name.get("text", "") if isinstance(name, dict) else str(name),
                "address": place.get("formattedAddress", ""),
                "phone": place.get("internationalPhoneNumber",
                         place.get("nationalPhoneNumber", "")),
                "website": place.get("websiteUri", ""),
                "rating": place.get("rating", ""),
                "reviews_count": place.get("userRatingCount", ""),
                "latitude": loc.get("latitude", ""),
                "longitude": loc.get("longitude", ""),
                "business_status": place.get("businessStatus", ""),
                "types": ", ".join(place.get("types", [])),
            })

    except requests.exceptions.HTTPError as e:
        error_msg = ""
        try:
            error_msg = e.response.json().get("error", {}).get("message", "")
        except Exception:
            error_msg = str(e)
        print(f"    Napaka API: {error_msg}")
    except Exception as e:
        print(f"    Napaka: {e}")

    return all_places


def collect_from_maps():
    """Zbere podjetja iz Google Maps Places API (New)."""

    if not GOOGLE_MAPS_API_KEY:
        print("NAPAKA: GOOGLE_MAPS_API_KEY ni nastavljen.")
        print("Nastavi ga v .env datoteki ali config.py")
        return []

    all_businesses = []
    seen = set()

    for location in SEARCH_LOCATIONS:
        for category in SEARCH_CATEGORIES:
            query = f"{category} {location}"
            print(f"  Iscem: {query}")

            places = search_places(query)

            for place in places:
                # Preskok duplikatov po place_id
                pid = place["place_id"]
                if pid in seen:
                    continue
                seen.add(pid)

                business = {
                    "source": "google_maps",
                    "name": place["name"],
                    "address": place["address"],
                    "phone": place["phone"],
                    "website": place["website"],
                    "google_rating": place["rating"],
                    "google_reviews_count": place["reviews_count"],
                    "place_id": pid,
                    "category": category,
                    "location": location,
                    "latitude": place["latitude"],
                    "longitude": place["longitude"],
                    "business_status": place["business_status"],
                }
                all_businesses.append(business)

            print(f"    Najdeno: {len(places)} ({len(all_businesses)} skupaj)")

            # Spoštuj rate limit
            time.sleep(0.3)

    return all_businesses


def save_businesses(businesses, filename="businesses_maps.csv"):
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
    print("=== Google Maps zbiralnik ===")
    businesses = collect_from_maps()
    if businesses:
        save_businesses(businesses)
    print(f"Skupaj: {len(businesses)} podjetij")

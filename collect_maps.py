"""
GRAFEIO Lead Crawler — Google Maps zbiralnik
=============================================
Isce podjetja po kategoriji in lokaciji prek Google Maps Places API.
"""

import csv
import os
import time
import googlemaps
from config import (
    GOOGLE_MAPS_API_KEY,
    SEARCH_CATEGORIES,
    SEARCH_LOCATIONS,
    MAPS_MAX_RESULTS,
    OUTPUT_DIR,
)


def collect_from_maps():
    """Zbere podjetja iz Google Maps Places API."""

    if not GOOGLE_MAPS_API_KEY:
        print("NAPAKA: GOOGLE_MAPS_API_KEY ni nastavljen.")
        print("Nastavi ga v .env datoteki ali config.py")
        return []

    gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)
    all_businesses = []
    seen = set()

    for location in SEARCH_LOCATIONS:
        for category in SEARCH_CATEGORIES:
            query = f"{category} {location}"
            print(f"  Iscem: {query}")

            try:
                # Text search vrne vec podatkov kot nearby search
                results = gmaps.places(query=query, language="sl")

                for place in results.get("results", [])[:MAPS_MAX_RESULTS]:
                    place_id = place.get("place_id", "")

                    # Preskok duplikatov
                    if place_id in seen:
                        continue
                    seen.add(place_id)

                    # Pridobi podrobnosti (website, phone)
                    details = {}
                    try:
                        details = gmaps.place(
                            place_id,
                            fields=[
                                "name",
                                "formatted_address",
                                "formatted_phone_number",
                                "website",
                                "rating",
                                "user_ratings_total",
                                "geometry",
                                "types",
                                "business_status",
                            ],
                            language="sl",
                        ).get("result", {})
                    except Exception as e:
                        print(f"    Opozorilo: ni podrobnosti za {place.get('name')}: {e}")

                    business = {
                        "source": "google_maps",
                        "name": details.get("name", place.get("name", "")),
                        "address": details.get(
                            "formatted_address",
                            place.get("formatted_address", ""),
                        ),
                        "phone": details.get("formatted_phone_number", ""),
                        "website": details.get("website", ""),
                        "google_rating": details.get(
                            "rating", place.get("rating", "")
                        ),
                        "google_reviews_count": details.get(
                            "user_ratings_total",
                            place.get("user_ratings_total", ""),
                        ),
                        "place_id": place_id,
                        "category": category,
                        "location": location,
                        "latitude": place.get("geometry", {})
                        .get("location", {})
                        .get("lat", ""),
                        "longitude": place.get("geometry", {})
                        .get("location", {})
                        .get("lng", ""),
                        "business_status": details.get("business_status", ""),
                    }
                    all_businesses.append(business)

                # Spoštuj rate limit
                time.sleep(0.3)

            except Exception as e:
                print(f"    Napaka pri iskanju '{query}': {e}")

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

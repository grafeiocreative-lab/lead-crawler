"""
GRAFEIO Lead Crawler — Konfiguracija
=====================================
Kopiraj ta file kot config.py in vnesi svoje API kljuce.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Google Maps Places API
# Pridobi na: https://console.cloud.google.com/apis/credentials
# Vklopi: Places API (New) ali Places API
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# Kategorije za iskanje (Google Maps query)
SEARCH_CATEGORIES = [
    # Zdravstvo in telo
    "zobozdravnik",
    "zobotehnik",
    "fizioterapija",
    "masažni salon",
    # Lepota in nega
    "kozmetični salon",
    "manikura pedikura",
    "frizerski salon",
    "salon za obrvi trepalnice",
    # Živali
    "pasji salon",
    # Avto
    "avto mehanik",
    "avto kleparstvo lakirnica",
    "avto elektrika",
    "vulkanizerstvo",
    # Obrt in gradbeništvo
    "mizar",
    "mizarstvo pohištvo po meri",
    "suhomontaža mavčne plošče",
    "vodovodar vodovodne inštalacije",
    "električar elektroinštalacije",
    "ključavničar",
    "slikopleskar pleskanje",
    "tesar",
    "krovstvo pokrivač",
    "keramičar polaganje ploščic",
    "steklar steklarstvo",
    "klima servis montaža",
]

# Lokacije za iskanje
SEARCH_LOCATIONS = [
    "Maribor",
    # "Ljubljana",
    # "Celje",
    # "Kranj",
    # "Koper",
    # "Novo mesto",
    # "Ptuj",
    # "Murska Sobota",
]

# Google Maps: max rezultatov na iskanje
MAPS_MAX_RESULTS = 20

# Diagnostika: timeout za HTTP zahteve (sekunde)
HTTP_TIMEOUT = 10

# Diagnostika: max stevilo internih linkov za preverjanje
MAX_INTERNAL_LINKS_CHECK = 5

# Lead scoring utezi
SCORING = {
    "no_website":           40,   # nima spletne strani sploh
    "no_ssl":               25,   # ni HTTPS
    "not_mobile":           20,   # ni viewport meta
    "slow_load":            15,   # > 5s load time
    "no_meta_description":  10,   # ni meta description
    "no_title":             10,   # ni title taga
    "old_copyright":        15,   # copyright starejsi od 2 let
    "no_favicon":            5,   # ni favicona
    "no_social":            10,   # ni socialnih linkov
    "broken_links":         15,   # broken interni linki
    "no_sitemap":            5,   # ni sitemap.xml
    "no_robots":             5,   # ni robots.txt
    "no_h1":                 5,   # ni H1 taga
    "images_no_alt":        10,   # slike brez alt
    "low_google_rating":    10,   # Google ocena < 4.0
    "few_google_reviews":   10,   # manj kot 10 Google recenzij
}

# Output
OUTPUT_DIR = "output"

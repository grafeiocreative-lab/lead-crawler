"""
GRAFEIO Lead Crawler — SKD mapiranje
======================================
Povezava iskalnih kategorij s SKD 2025 kodami.

Uporaba:
- Za kasnejso integracijo z AJPES restPrsInfo API
- Za oznacevanje leadov s formalno dejavnostjo
- Za filtriranje OPSI dumpa po SKD kodah

SKD 2025 kode relevantne za Grafeio ciljne stranke.
Vir: spot.gov.si, stat.si/statweb

Opomba: SKD 2025 je od januarja 2025 nadomestil SKD 2008.
Nekatere kode so se spremenile. Tukaj so SKD 2025 kode.
"""

# Mapiranje: SKD koda -> opis -> iskalni pojmi za Google Maps
SKD_MAP = {
    # ZDRAVSTVO
    "86.230": {
        "opis": "Zobozdravstvena dejavnost",
        "iskalni_pojmi": ["zobozdravnik", "zobotehnik", "ortodont", "dentalna klinika"],
    },
    "86.909": {
        "opis": "Druge dejavnosti za zdravje",
        "iskalni_pojmi": ["fizioterapija", "kiropraktik", "osteopat", "logoped"],
    },
    "86.210": {
        "opis": "Splošna zunajbolnišnična zdravstvena dejavnost",
        "iskalni_pojmi": ["ambulanta", "zdravnik"],
    },
    "86.220": {
        "opis": "Specialistična zunajbolnišnična zdravstvena dejavnost",
        "iskalni_pojmi": ["specialist", "psihiater"],
    },

    # LEPOTA IN NEGA
    "96.021": {
        "opis": "Frizerska dejavnost",
        "iskalni_pojmi": ["frizer", "frizerski salon", "brivec", "barbershop"],
    },
    "96.022": {
        "opis": "Kozmetična in pedikerska dejavnost",
        "iskalni_pojmi": [
            "kozmetični salon", "manikura", "pedikura",
            "salon za nohte", "obrvi in trepalnice",
        ],
    },
    "96.040": {
        "opis": "Dejavnosti za nego telesa",
        "iskalni_pojmi": [
            "masažni salon", "masaža", "solarij",
            "salon za depilacijo", "salon za nego telesa",
        ],
    },
    "96.091": {
        "opis": "Dejavnost tetoviranje in piercing",
        "iskalni_pojmi": ["tetoviranje", "piercing", "permanentni make-up"],
    },

    # ŽIVALI
    "75.000": {
        "opis": "Veterinarska dejavnost",
        "iskalni_pojmi": ["veterinar", "veterinarska ambulanta"],
    },
    "96.092": {
        "opis": "Dejavnost oskrbe hišnih živali",
        "iskalni_pojmi": ["pasji salon", "grooming", "pasja šola", "hotel za živali"],
    },

    # AVTO
    "45.200": {
        "opis": "Vzdrževanje in popravila motornih vozil",
        "iskalni_pojmi": [
            "avtoservis", "avto mehanik", "avtoklepar",
            "avtoličar", "avtoelektrika", "vulkanizerstvo",
        ],
    },
    "45.400": {
        "opis": "Trgovina z motocikli in popravila",
        "iskalni_pojmi": ["servis motornih koles"],
    },
    "52.212": {
        "opis": "Vleka vozil in podobne storitve",
        "iskalni_pojmi": ["avtovleka", "avtodvigala"],
    },

    # GRADBENI OBRTNIKI
    "43.210": {
        "opis": "Inštaliranje električnih napeljav in naprav",
        "iskalni_pojmi": ["elektroinštalater", "električar"],
    },
    "43.220": {
        "opis": "Inštaliranje vodovodnih, plinovodnih in ogrevalnih napeljav",
        "iskalni_pojmi": ["vodoinštalater", "vodovodar"],
    },
    "43.290": {
        "opis": "Drugo inštaliranje pri gradnjah",
        "iskalni_pojmi": [
            "klima servis", "toplotne črpalke", "prezračevalni sistemi",
            "alarm montaža", "sončne elektrarne",
        ],
    },
    "43.310": {
        "opis": "Fasaderska in štukaterska dela",
        "iskalni_pojmi": ["fasaderstvo", "izolacije"],
    },
    "43.320": {
        "opis": "Vgrajevanje stavbnega pohištva",
        "iskalni_pojmi": ["okna in vrata", "senčila rolete", "garažna vrata"],
    },
    "43.330": {
        "opis": "Oblaganje tal in sten",
        "iskalni_pojmi": ["keramičar", "polaganje ploščic", "parketar"],
    },
    "43.341": {
        "opis": "Steklarska dela",
        "iskalni_pojmi": ["steklarstvo", "steklarska delavnica"],
    },
    "43.342": {
        "opis": "Pleskarska in zastekljevalna dela",
        "iskalni_pojmi": ["slikopleskar", "pleskanje"],
    },
    "43.910": {
        "opis": "Postavljanje ostrešij in krovska dela",
        "iskalni_pojmi": ["krovstvo", "kleparstvo"],
    },
    "81.220": {
        "opis": "Drugo čiščenje stavb, industrijskih naprav in opreme",
        "iskalni_pojmi": ["dimnikar", "dimnikarstvo"],
    },

    # MIZARSTVO IN LES
    "16.230": {
        "opis": "Stavbno mizarstvo in tesarstvo",
        "iskalni_pojmi": ["mizar", "mizarstvo", "tesar"],
    },

    # KLJUČAVNIČARSTVO IN KOVINARSTVO
    "25.500": {
        "opis": "Kovanje, stiskanje, vtiskovanje in valjanje kovin",
        "iskalni_pojmi": ["kovač", "kovaštvo", "umetno kovaštvo"],
    },
    "25.720": {
        "opis": "Proizvodnja ključavnic, okovij",
        "iskalni_pojmi": ["ključavničar", "ključavničarstvo"],
    },

    # TRADICIONALNE OBRTI
    "32.120": {
        "opis": "Proizvodnja nakita in podobnih izdelkov",
        "iskalni_pojmi": ["zlatarstvo", "zlatar", "graverstvo", "pozlata"],
    },
    "33.130": {
        "opis": "Popravila elektronskih in optičnih naprav",
        "iskalni_pojmi": ["urar", "urarstvo"],
    },
    "15.200": {
        "opis": "Proizvodnja obutve",
        "iskalni_pojmi": ["čevljar", "čevljarstvo", "popravilo obutve"],
    },
    "14.130": {
        "opis": "Proizvodnja drugih oblačil",
        "iskalni_pojmi": ["šivilja", "krojač", "popravilo oblačil"],
    },
    "31.090": {
        "opis": "Proizvodnja drugega pohištva",
        "iskalni_pojmi": ["tapetnik", "tapetništvo", "restavriranje pohištva"],
    },
    "15.120": {
        "opis": "Proizvodnja potovalnih kovčkov, torb in podobnih izdelkov, sedlarskih izdelkov",
        "iskalni_pojmi": ["sedlar", "sedlarstvo"],
    },

    # ČIŠČENJE
    "81.210": {
        "opis": "Splošno čiščenje stavb",
        "iskalni_pojmi": [
            "čistilni servis", "čiščenje poslovnih prostorov",
            "čiščenje stanovanj", "pranje oken",
        ],
    },
    "96.010": {
        "opis": "Dejavnost pralnic in kemičnih čistilnic",
        "iskalni_pojmi": ["kemična čistilnica", "čistilnica oblačil", "pranje preprog"],
    },
    "81.291": {
        "opis": "Dezinfekcija, dezinsekcija in deratizacija",
        "iskalni_pojmi": ["dezinfekcija", "deratizacija", "dezinsekcija"],
    },
    "81.300": {
        "opis": "Urejanje in vzdrževanje zelenih površin",
        "iskalni_pojmi": ["vrtnarstvo", "urejanje okolice", "vzdrževanje zelenic"],
    },

    # FOTO IN TISK
    "74.200": {
        "opis": "Fotografska dejavnost",
        "iskalni_pojmi": ["fotograf", "fotografski studio", "poročni fotograf"],
    },
    "18.120": {
        "opis": "Drugo tiskanje",
        "iskalni_pojmi": ["tiskarna", "tiskarstvo"],
    },

    # HRANA
    "10.710": {
        "opis": "Proizvodnja kruha, svežega peciva in slaščic",
        "iskalni_pojmi": ["pekarna", "slaščičarna", "cukrarna"],
    },
    "56.210": {
        "opis": "Priložnostna priprava in dostava jedi",
        "iskalni_pojmi": ["catering", "dostava hrane"],
    },
    "10.130": {
        "opis": "Proizvodnja mesnih izdelkov",
        "iskalni_pojmi": ["mesar", "mesnica"],
    },
}


def get_skd_for_query(query):
    """Poizkusi najti SKD kodo za iskalni pojem."""
    query_lower = query.lower().strip()
    for skd_code, info in SKD_MAP.items():
        for pojem in info["iskalni_pojmi"]:
            if pojem.lower() in query_lower or query_lower in pojem.lower():
                return skd_code, info["opis"]
    return None, None


def get_all_search_terms():
    """Vrne vse iskalne pojme iz SKD mapiranja."""
    terms = []
    for info in SKD_MAP.values():
        terms.extend(info["iskalni_pojmi"])
    return terms


def get_skd_codes_for_sector(sector_keywords):
    """Vrne SKD kode ki ustrezajo kljucnim besedam sektorja."""
    matches = []
    for skd_code, info in SKD_MAP.items():
        opis_lower = info["opis"].lower()
        for kw in sector_keywords:
            if kw.lower() in opis_lower:
                matches.append((skd_code, info["opis"]))
                break
    return matches


if __name__ == "__main__":
    print(f"SKD mapiranih kod: {len(SKD_MAP)}")
    print(f"Iskalnih pojmov: {len(get_all_search_terms())}")

    # Test
    test_queries = [
        "zobozdravnik",
        "zlatar",
        "čevljar",
        "čistilni servis",
        "avtodvigala",
        "šivilja",
    ]
    print("\nTest mapiranja:")
    for q in test_queries:
        code, desc = get_skd_for_query(q)
        print(f"  {q} -> {code} ({desc})")

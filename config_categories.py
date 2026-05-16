"""
GRAFEIO Lead Crawler — Razširjene kategorije iskanja
======================================================
Kategorije so izpeljane iz SKD 2025 šifranta in prilagojene
za iskanje na Google Maps v slovenščini.

Organizirane po sektorjih za lažje upravljanje.
Vsaka kategorija je iskalni pojem, ki ga Maps razume.

Dodaj ali odstrani po potrebi. Google Maps tolerira
slovenščino in vrne rezultate tudi za splošne pojme.
"""

# === ZDRAVSTVO IN TERAPIJA ===
ZDRAVSTVO = [
    "zobozdravnik",
    "zobotehnik",
    "ortodont",
    "zobni laboratorij",
    "fizioterapija",
    "fizioterapevt",
    "kiropraktik",
    "osteopat",
    "logoped",
    "psiholog",
    "psihoterapevt",
    "delovna terapija",
    "medicinska pedikura",
    "podolog",
    "optik",
    "optika",
    "ortopedska obutev",
    "slušni aparati",
    "zobna protetika",
    "dentalna klinika",
]

# === LEPOTA IN NEGA ===
LEPOTA = [
    "kozmetični salon",
    "frizerski salon",
    "frizer",
    "brivec",
    "manikura pedikura",
    "manikura",
    "pedikura",
    "salon za nohte",
    "obrvi in trepalnice",
    "trajno lakiranje nohtov",
    "masažni salon",
    "masaža",
    "refleksoterapija",
    "salon za depilacijo",
    "solarij",
    "tetoviranje",
    "piercing",
    "salon za nego telesa",
    "permanentni make-up",
    "mikropigmentacija",
    "barbershop",
]

# === ŽIVALI ===
ZIVALI = [
    "pasji salon",
    "grooming psi",
    "veterinar",
    "veterinarska ambulanta",
    "pasja šola",
    "hotel za živali",
    "pasji hotel",
    "trimanje psov",
]

# === AVTO IN MEHANIKA ===
AVTO = [
    "avto mehanik",
    "avtoservis",
    "avtopralnica",
    "vulkanizerstvo",
    "avtoelektrika",
    "avtoklepar",
    "avtoličar",
    "avtovleka",
    "avtodvigala",
    "servis klima naprav avto",
    "menjava olja avto",
    "avtodiagnostika",
    "popravilo motorjev",
    "servis motornih koles",
    "kolesarski servis",
    "servis delovnih strojev",
]

# === GRADBENI IN HIŠNI OBRTNIKI ===
GRADBENIKI = [
    "ključavničar",
    "ključavničarstvo",
    "steklarska delavnica",
    "steklarstvo",
    "vodovodar",
    "vodoinštalater",
    "elektroinštalater",
    "električar",
    "keramičar",
    "polaganje ploščic",
    "parketar",
    "polaganje parketa",
    "mizar",
    "mizarstvo",
    "tesar",
    "kleparstvo in krovna dela",
    "krovstvo",
    "slikopleskar",
    "pleskanje",
    "fasaderstvo",
    "izolacije",
    "toplotne črpalke montaža",
    "dimnikar",
    "dimnikarstvo",
    "alarm montaža",
    "varnostni sistemi montaža",
    "okna in vrata montaža",
    "senčila rolete montaža",
    "garažna vrata servis",
    "klima servis",
    "prezračevalni sistemi",
    "protipožarna zaščita",
    "sončne elektrarne montaža",
]

# === TRADICIONALNE OBRTI ===
OBRTI = [
    "zlatarstvo",
    "zlatar",
    "urarstvo",
    "urar",
    "čevljar",
    "čevljarstvo",
    "popravilo obutve",
    "šivilja",
    "šiviljstvo",
    "krojač",
    "krojačica",
    "popravilo oblačil",
    "tapetništvo",
    "tapetnik",
    "sedlar",
    "sedlarstvo",
    "lončar",
    "lončarstvo",
    "kovač",
    "kovaštvo",
    "umetno kovaštvo",
    "restavriranje pohištva",
    "pozlata",
    "graverstvo",
    "knjigovez",
    "knjigovezništvo",
]

# === ČIŠČENJE IN VZDRŽEVANJE ===
CISCENJE = [
    "čistilni servis",
    "čiščenje poslovnih prostorov",
    "čiščenje stanovanj",
    "industrijski čistilni servis",
    "pranje oken",
    "globinsko čiščenje",
    "kemična čistilnica",
    "čistilnica oblačil",
    "pranje preprog",
    "dezinfekcija prostorov",
    "deratizacija",
    "dezinsekcija",
    "vzdrževanje zelenic",
    "vrtnarstvo",
    "urejanje okolice",
    "arborist",
    "čiščenje fasad",
    "visokotlačno čiščenje",
]

# === FOTO, VIDEO, KREATIVA ===
KREATIVA = [
    "fotograf",
    "fotografski studio",
    "poročni fotograf",
    "tiskarstvo",
    "tiskarna",
    "oglaševalska agencija",
    "grafično oblikovanje",
    "tiskarstvo velikih formatov",
    "reklamni napisi",
    "neonski napisi",
    "izdelava pečatov",
    "tampon tisk",
    "vezenje",
    "sitotisk",
    "kaligrafija",
]

# === HRANA IN GOSTINSTVO (mikro) ===
HRANA = [
    "pekarna",
    "slaščičarna",
    "cukrarna",
    "catering",
    "dostava hrane",
    "torte po naročilu",
    "mesar",
    "mesnica",
    "pražarna kave",
    "čajnica",
    "sladoledarna",
    "bio trgovina",
    "ekološka kmetija z dostavo",
]

# === OSTALE STORITVENE ===
OSTALO = [
    "ključi in ključavnice",
    "brusilni servis",
    "ostrenje nožev",
    "nožarstvo",
    "popravilo bele tehnike",
    "popravilo telefonov",
    "računalniški servis",
    "servis šivalnih strojev",
    "selitve",
    "selitveni servis",
    "dostava in kurirska služba",
    "skladiščenje",
    "čuvanje otrok",
    "varstvo otrok na domu",
    "inštrukcije",
    "učna pomoč",
    "glasbena šola zasebna",
    "šola tujih jezikov",
    "avtošola",
    "jadralna šola",
    "šola jahanja",
    "fitnes studio",
    "joga studio",
    "pilates studio",
    "borilne veščine",
    "plesna šola",
]


def get_all_categories():
    """Vrne vse kategorije kot en seznam."""
    return (
        ZDRAVSTVO
        + LEPOTA
        + ZIVALI
        + AVTO
        + GRADBENIKI
        + OBRTI
        + CISCENJE
        + KREATIVA
        + HRANA
        + OSTALO
    )


def get_categories_by_sector(sector_name):
    """Vrne kategorije za podan sektor.

    Možni sektorji: zdravstvo, lepota, zivali, avto, gradbeniki,
    obrti, ciscenje, kreativa, hrana, ostalo
    """
    sectors = {
        "zdravstvo": ZDRAVSTVO,
        "lepota": LEPOTA,
        "zivali": ZIVALI,
        "avto": AVTO,
        "gradbeniki": GRADBENIKI,
        "obrti": OBRTI,
        "ciscenje": CISCENJE,
        "kreativa": KREATIVA,
        "hrana": HRANA,
        "ostalo": OSTALO,
    }
    return sectors.get(sector_name.lower(), [])


def get_sector_names():
    """Vrne seznam imen vseh sektorjev."""
    return [
        "zdravstvo",
        "lepota",
        "zivali",
        "avto",
        "gradbeniki",
        "obrti",
        "ciscenje",
        "kreativa",
        "hrana",
        "ostalo",
    ]


# Statistika
if __name__ == "__main__":
    all_cats = get_all_categories()
    print(f"Skupaj kategorij: {len(all_cats)}")
    for name in get_sector_names():
        cats = get_categories_by_sector(name)
        print(f"  {name}: {len(cats)}")

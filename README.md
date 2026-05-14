# GRAFEIO Lead Crawler

Isci podjetja brez digitalne prisotnosti. Diagnosticiraj njihove spletne strani. Oceni potencialne stranke.

## Kaj naredi

1. **Zbere podjetja** iz Google Maps in bizi.si po kategorijah (zobozdravniki, fizioterapevti, kozmeticni saloni ...)
2. **Preveri spletno stran** vsakega podjetja: SSL, mobilnost, hitrost, SEO, broken links, copyright leto, socialni linki
3. **Oceni leade**: HOT / WARM / LOW z razlogi

## Namestitev

```bash
cd grafeio-lead-crawler
pip install -r requirements.txt
cp .env.example .env
# Uredi .env in vnesi GOOGLE_MAPS_API_KEY
```

### Google Maps API kljuc

1. Pojdi na https://console.cloud.google.com/apis/credentials
2. Ustvari nov API kljuc
3. Vklopi "Places API" (ali "Places API (New)")
4. Kopiraj kljuc v `.env`

Brezplacna kvota: 200 USD/mesec kredit (dovolj za tisoce iskanj).

## Uporaba

### Celoten pipeline
```bash
python main.py all
```
Zbere iz obeh virov, diagnosticira, oceni. Rezultat: `output/leads_scored.csv`

### Po korakih
```bash
python main.py collect-maps     # Samo Google Maps
python main.py collect-bizi     # Samo bizi.si
python main.py collect          # Oboje + zdruzevanje
python main.py diagnose         # Diagnostika (rabi businesses CSV)
python main.py score            # Scoring (rabi diagnostics CSV)
```

### Hitra diagnostika ene strani
```bash
python main.py quick https://primer-zobozdravnika.si
```
Takoj izpise diagnostiko in lead score.

## Output

Vse datoteke v `output/` mapi:

| Datoteka | Vsebina |
|---|---|
| `businesses_maps.csv` | Podjetja iz Google Maps |
| `businesses_bizi.csv` | Podjetja iz bizi.si |
| `businesses_all.csv` | Zdruzeno, deduplicirano |
| `diagnostics.csv` | Diagnostika spletnih strani |
| `leads_scored.csv` | Koncni rezultat s scoring |

## Konfiguracija

Uredi `config.py`:

- `SEARCH_CATEGORIES`: katere panoge iscemo
- `SEARCH_LOCATIONS`: katera mesta
- `SCORING`: utezi za posamezne kriterije
- `HTTP_TIMEOUT`: timeout za preverjanje strani

## Lead scoring

| Kriterij | Tocke | Pomen |
|---|---|---|
| Nima spletne strani | +40 | Najbolj vroce |
| Ni SSL | +25 | Neprofesionalno |
| Ni mobilno prilagojena | +20 | Izgublja stranke |
| Pocasno nalaganje (>5s) | +15 | Slaba izkusnja |
| Star copyright (>2 leti) | +15 | Zanemarjena stran |
| Broken links | +15 | Zanemarjena stran |
| Ni meta opisa | +10 | Slab SEO |
| Ni naslova | +10 | Slab SEO |
| Ni socialnih linkov | +10 | Ni digitalne prisotnosti |
| Slike brez alt | +10 | Slab SEO |
| Google ocena < 4.0 | +10 | Potencialne tezave |
| < 10 Google recenzij | +10 | Slaba vidnost |
| Ni favicona | +5 | Detajl |
| Ni sitemap.xml | +5 | Slab SEO |
| Ni robots.txt | +5 | Slab SEO |
| Ni H1 naslova | +5 | Slab SEO |

### Klasifikacija

- **HOT** (60+): takoj kontaktiraj
- **WARM** (30 do 59): vredno pozornosti
- **LOW** (pod 30): stran je solidna, ni nujno

## Naslednji koraki

- [ ] Telegram/email alert za nove HOT leade
- [ ] Supabase baza namesto CSV
- [ ] Dashboard (React/Next.js)
- [ ] Periodicen cron job (tedensko skeniranje)
- [ ] Generiranje PDF diagnosticnega porocila za stranko

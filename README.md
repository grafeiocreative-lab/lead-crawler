# Lead Crawler — Razširitev (maj 2026)

## Kaj je novo

### 1. `config_categories.py` — 196 iskalnih kategorij
Razširjen seznam obrtniških dejavnosti, organiziran po sektorjih:
- zdravstvo (20), lepota (21), živali (8), avto (16)
- gradbeniki (33), obrti (26), čiščenje (18)
- kreativa (15), hrana (13), ostalo (26)

Izpeljan iz SKD 2025 šifranta. Uporabi namesto starih 9 kategorij v `config.py`.

### 2. `enrich.py` — Obogatitev leadov
Nov korak v pipeline-u, ki se požene PO score.py:
- **Google Reviews Score (GRS):** ponderiran signal iz ocene in števila recenzij (0 do 100)
- **Golden Lead detekcija:** GBP profil + brez spletne strani + ocena 4.0+ + 20+ recenzij
- **Prioritetni signal (0 do 100):** kombiniran signal za Barbaro
- **Konkurenčni pregled:** analiza po mestih in dejavnostih (JSON + TXT)

### 3. `skd_mapping.py` — SKD kode za kategorije
41 SKD 2025 kod, mapirano na iskalne pojme. Za kasnejšo integracijo z AJPES restPrsInfo API.

## Maksimalno pokritje z brezplačno kvoto

```
196 kategorij × 31 lokacij = 6.076 klicev = 194 USD (kvota: 200 USD)
```

31 lokacij pokriva vseh 11 mestnih občin + 20 regionalnih središč.
To je ~85% slovenskega trga storitvenih dejavnosti.

**Pravilo:** poženi ENKRAT na mesec. Dvakrat = presežeš kvoto.
`preflight.py` te opozori če si že poganjal ta mesec.

## Integracija v obstoječi repo

### Korak 1: kopiraj datoteke
```bash
cd ~/Projects/grafeio/lead-crawler
cp ~/pot/do/config_categories.py .
cp ~/pot/do/enrich.py .
cp ~/pot/do/skd_mapping.py .
cp ~/pot/do/preflight.py .
```

Zamenjaj stari `config.py` z novim:
```bash
cp ~/pot/do/config.py .
```

### Korak 3: posodobi main.py
Dodaj `enrich` kot nov korak. V `if __name__` blok dodaj:

```python
elif cmd == "enrich":
    from enrich import enrich_leads, save_enriched, load_csv
    scored_file = os.path.join(OUTPUT_DIR, "leads_scored.csv")
    leads = load_csv(scored_file)
    enriched = enrich_leads(leads)
    save_enriched(enriched)

elif cmd == "report":
    from enrich import (
        enrich_leads, save_enriched, load_csv,
        build_competitive_report, save_competitive_report,
        save_competitive_report_txt,
    )
    scored_file = os.path.join(OUTPUT_DIR, "leads_scored.csv")
    leads = load_csv(scored_file)
    enriched = enrich_leads(leads)
    save_enriched(enriched)
    report = build_competitive_report(enriched)
    save_competitive_report(report)
    save_competitive_report_txt(report)
```

In v `all` pipeline dodaj enrich za score:
```python
# ... po score ...
enriched = enrich_leads(scored)
save_enriched(enriched)
```

### Korak 4: poženi
```bash
# NAJPREJ preveri stroške in status
python3 preflight.py

# Ko si prepričana, poženi z --run
python3 preflight.py --run

# ALI po korakih:
python3 main.py collect         # zberi iz Maps
python3 main.py diagnose        # diagnosticiraj strani
python3 main.py score           # oceni leade
python3 enrich.py output/leads_scored.csv --report   # obogati + report
```

## Novi output fajli

| Datoteka | Vsebina |
|---|---|
| `output/leads_enriched.csv` | Obogateni leadi z GRS, prioriteto, golden flag |
| `output/competitive_report.json` | Konkurenčni pregled (strojno berljiv) |
| `output/competitive_report.txt` | Konkurenčni pregled (za Barbaro) |

## Lead prioritetna formula

| Signal | Točke |
|---|---|
| Brez spletne strani | +40 |
| GBP profil brez strani | +15 |
| Visoka ocena (4.5+) | +10 |
| Veliko recenzij (30+) | +15 |
| Golden lead bonus | +20 |
| Obstoječi HOT | +10 |
| Obstoječi WARM | +5 |

**Golden lead** = brez strani + ocena 4.0+ + 20+ recenzij. To so podjetja z dokazanim povpraševanjem, ki nimajo digitalnega kanala.

## AJPES: naslednji korak

Ko bo potreba po uradnih podatkih (matična, davčna, datum ustanovitve):
1. Registracija na ajpes.si (brezplačna)
2. Naročilnica za restPrsInfo API
3. `skd_mapping.py` že ima mapiranje za iskanje po SKD kodi

Testno okolje (Swagger): na AJPES strani, vrača 3 rezultate.
Produkcijsko: po odobritvi naročilnice.

## Pošiljanje leadov v bazo (od 25. 10. 2026)

Dashboard ne bere več datoteke `leads.json` iz repozitorija — podatki so v Supabase
(tabeli `leads` in `leads_meta`) in vidni samo prijavljenima naslovoma lastnice.

Po vsakem crawlu jih pošlji v bazo:

```bash
python push_to_supabase.py                 # prebere output/leads_scored.csv
python push_to_supabase.py --json leads.json
python push_to_supabase.py --dry-run       # preveri brez pošiljanja
```

V `.env` morata biti `SUPABASE_URL` in `SUPABASE_SERVICE_KEY` (glej `.env.example`).
Ključ je skrbniški: ostane na tem računalniku in ne gre v git.

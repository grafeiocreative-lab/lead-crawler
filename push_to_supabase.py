#!/usr/bin/env python3
"""Pošlje leade v Supabase, da jih dashboard bere iz baze (ne iz javne datoteke).

Zakaj: do 25. 10. 2026 je dashboard bral leads.json, ki je stal v repozitoriju in bil
zato javno dostopen. Zdaj so podatki v tabelah `leads` in `leads_meta` in vidni samo
prijavljenima naslovoma lastnice.

Uporaba:
    python push_to_supabase.py                       # prebere output/leads_scored.csv
    python push_to_supabase.py --csv output/drug.csv
    python push_to_supabase.py --json leads.json     # stara oblika izvoza za dashboard
    python push_to_supabase.py --dry-run             # samo pokaže, ne pošlje

Ključa se bereta iz .env v isti mapi:
    SUPABASE_URL=https://cseifhrfmemvizwbmyjd.supabase.co
    SUPABASE_SERVICE_KEY=...            (skrbniški ključ; NIKOLI v git)
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

KOREN = Path(__file__).resolve().parent
TABELA = "leads"
META_TABELA = "leads_meta"
KOS = 500


def preberi_env() -> dict[str, str]:
    """Preprosto branje .env (brez zunanjih knjižnic)."""
    vrednosti: dict[str, str] = {}
    pot = KOREN / ".env"
    if pot.exists():
        for vrstica in pot.read_text(encoding="utf-8").splitlines():
            vrstica = vrstica.strip()
            if not vrstica or vrstica.startswith("#") or "=" not in vrstica:
                continue
            kljuc, vrednost = vrstica.split("=", 1)
            vrednosti[kljuc.strip()] = vrednost.strip().strip('"').strip("'")
    vrednosti.setdefault("SUPABASE_URL", os.environ.get("SUPABASE_URL", ""))
    vrednosti.setdefault("SUPABASE_SERVICE_KEY", os.environ.get("SUPABASE_SERVICE_KEY", ""))
    return vrednosti


def preberi_csv(pot: Path) -> list[dict]:
    with pot.open(encoding="utf-8-sig", newline="") as f:
        return [dict(vrstica) for vrstica in csv.DictReader(f)]


def preberi_json(pot: Path) -> tuple[list[dict], dict]:
    podatki = json.loads(pot.read_text(encoding="utf-8"))
    if isinstance(podatki, dict) and isinstance(podatki.get("leads"), list):
        meta = {k: v for k, v in podatki.items() if k != "leads"}
        return podatki["leads"], meta
    if isinstance(podatki, list):
        return podatki, {}
    raise SystemExit(f"Ne razumem oblike datoteke {pot}.")


def kljuc(vodic: dict) -> str:
    """Stabilen ključ: place_id, sicer zgoščena kombinacija imena in naslova."""
    pid = (vodic.get("place_id") or "").strip()
    if pid:
        return pid
    osnova = "|".join([
        (vodic.get("name") or "").strip().lower(),
        (vodic.get("address") or "").strip().lower(),
    ])
    return "na:" + hashlib.md5(osnova.encode("utf-8")).hexdigest()[:20]


def pocisti(vodic: dict) -> dict:
    """Odstrani prazne vrednosti in odvečne presledke, ohrani vsa polja."""
    ociscen = {}
    for kljuc_polja, vrednost in vodic.items():
        if kljuc_polja is None:
            continue
        ime = str(kljuc_polja).strip()
        if isinstance(vrednost, str):
            vrednost = vrednost.strip()
        if vrednost in ("", None):
            continue
        ociscen[ime] = vrednost
    return ociscen


def izracunaj_meta(vodici: list[dict], izvorna_meta: dict | None = None) -> dict:
    izvorna_meta = izvorna_meta or {}
    hot = sum(1 for v in vodici if str(v.get("classification", "")).upper() == "HOT")
    warm = sum(1 for v in vodici if str(v.get("classification", "")).upper() == "WARM")
    low = sum(1 for v in vodici if str(v.get("classification", "")).upper() == "LOW")
    golden = sum(1 for v in vodici if str(v.get("golden_lead", "")).upper() in ("DA", "TRUE", "1"))
    return {
        "generated": izvorna_meta.get("generated") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total": len(vodici),
        "hot": izvorna_meta.get("hot", hot),
        "warm": izvorna_meta.get("warm", warm),
        "low": izvorna_meta.get("low", low),
        "golden": izvorna_meta.get("golden", golden),
        "vir": izvorna_meta.get("vir", "lead-crawler"),
    }


def poslji(url: str, kljuc_api: str, tabela: str, vrstice: list[dict], na_konflikt: str) -> None:
    telo = json.dumps(vrstice, ensure_ascii=False).encode("utf-8")
    zahteva = urllib.request.Request(
        f"{url}/rest/v1/{tabela}?on_conflict={na_konflikt}",
        data=telo,
        method="POST",
        headers={
            "apikey": kljuc_api,
            "Authorization": f"Bearer {kljuc_api}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
    )
    for poskus in range(3):
        try:
            urllib.request.urlopen(zahteva, timeout=180)
            return
        except urllib.error.HTTPError as e:
            podrobnost = e.read().decode("utf-8", "replace")[:300]
            if e.code in (429, 500, 502, 503, 504) and poskus < 2:
                time.sleep(2 * (poskus + 1))
                continue
            raise SystemExit(f"Napaka {e.code} pri pošiljanju v {tabela}: {podrobnost}")
        except urllib.error.URLError as e:
            if poskus < 2:
                time.sleep(2 * (poskus + 1))
                continue
            raise SystemExit(f"Povezava ni uspela: {e}")


def main() -> int:
    okolje = preberi_env()
    url = okolje.get("SUPABASE_URL", "").rstrip("/")
    kljuc_api = okolje.get("SUPABASE_SERVICE_KEY", "")

    parser = argparse.ArgumentParser(description="Pošlje leade v Supabase.")
    izbira = parser.add_mutually_exclusive_group()
    izbira.add_argument("--csv", type=Path, default=None, help="vhodna CSV datoteka")
    izbira.add_argument("--json", type=Path, default=None, help="vhodna JSON datoteka (stara oblika)")
    parser.add_argument("--dry-run", action="store_true", help="ne pošlji, samo pokaži")
    args = parser.parse_args()

    if args.json:
        vhod = args.json
        if not vhod.exists():
            raise SystemExit(f"Datoteke ni: {vhod}")
        vodici, izvorna_meta = preberi_json(vhod)
    else:
        vhod = args.csv or (KOREN / "output" / "leads_scored.csv")
        if not vhod.exists():
            raise SystemExit(f"Datoteke ni: {vhod}. Zaženi najprej crawl ali navedi --csv/--json.")
        vodici, izvorna_meta = preberi_csv(vhod), {}

    if not vodici:
        raise SystemExit("Vhod je prazna — nič za poslati.")

    vrstice = []
    for vodic in vodici:
        podatki = pocisti(vodic)
        if not podatki.get("name"):
            continue
        vrstice.append({"id": kljuc(podatki), "data": podatki})

    meta = izracunaj_meta([r["data"] for r in vrstice], izvorna_meta)
    print(f"Vhod: {vhod} — {len(vrstice)} leadov")
    print(f"Povzetek: skupaj {meta['total']}, HOT {meta['hot']}, WARM {meta['warm']}, "
          f"LOW {meta['low']}, golden {meta['golden']}")

    if args.dry_run:
        print("Suho: nič ni bilo poslano. Primer vrstice:")
        print(json.dumps(vrstice[0], ensure_ascii=False)[:400])
        return 0

    if not url or not kljuc_api:
        raise SystemExit(
            "Manjka SUPABASE_URL ali SUPABASE_SERVICE_KEY.\n"
            "Dodaj ju v .env (glej .env.example). Ključ naj ne gre v git."
        )

    poslano = 0
    for i in range(0, len(vrstice), KOS):
        kos = vrstice[i:i + KOS]
        poslji(url, kljuc_api, TABELA, kos, "id")
        poslano += len(kos)
        print(f"  poslano {poslano}/{len(vrstice)}")

    poslji(url, kljuc_api, META_TABELA, [{"id": "main", "data": meta}], "id")
    print(f"Končano: {poslano} leadov v bazi, povzetek osvežen.")
    print("Dashboard jih zdaj bere iz baze (prijava je obvezna).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""
GRAFEIO Lead Crawler — Zdruzi e-maile v dashboard leads.json
================================================================
Zdruzi:
  1. output/leads_enriched.csv (email, email_source) — s crawlanjem lastne strani
  2. output/web_search_emails.csv (web_email, ...) — z zunanjim spletnim iskanjem
       (samo za HOT/golden leade brez lastne strani)
v ../lead-dashboard/leads.json, ki ga bere dashboard.

Pred prepisom naredi varnostno kopijo (leads.json.bak).
NE pushne v git / ne deploya na Netlify — to je locen korak.

Uporaba:
    python3 merge_dashboard_emails.py
"""

import csv
import json
import os
import shutil

CRAWLER_OUTPUT = "output"
DASHBOARD_DIR = "../lead-dashboard"
LEADS_JSON = os.path.join(DASHBOARD_DIR, "leads.json")
ENRICHED_CSV = os.path.join(CRAWLER_OUTPUT, "leads_enriched.csv")
WEB_SEARCH_CSV = os.path.join(CRAWLER_OUTPUT, "web_search_emails.csv")
COMPANYWALL_CSV = os.path.join(CRAWLER_OUTPUT, "companywall_emails.csv")


def load_csv_index(filepath, key_fields=("place_id",), fallback_fields=("name", "address")):
    """Nalozi CSV in vrni dva indeksa: po place_id in po (name, address)."""
    by_pid = {}
    by_name_addr = {}
    if not os.path.exists(filepath):
        return by_pid, by_name_addr

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("place_id") or "").strip()
            if pid:
                by_pid[pid] = row
            key = (
                (row.get("name") or "").strip().lower(),
                (row.get("address") or "").strip().lower(),
            )
            if key[0]:
                by_name_addr[key] = row

    return by_pid, by_name_addr


def lookup(row_by_pid, row_by_name_addr, lead):
    pid = (lead.get("place_id") or "").strip()
    if pid and pid in row_by_pid:
        return row_by_pid[pid]
    key = ((lead.get("name") or "").strip().lower(), (lead.get("address") or "").strip().lower())
    return row_by_name_addr.get(key)


def main():
    if not os.path.exists(LEADS_JSON):
        print(f"NAPAKA: {LEADS_JSON} ne obstaja.")
        return

    print(f"Berem {ENRICHED_CSV} ...")
    enr_pid, enr_name = load_csv_index(ENRICHED_CSV)
    print(f"  {len(enr_pid)} po place_id, {len(enr_name)} po imenu+naslovu")

    print(f"Berem {WEB_SEARCH_CSV} ...")
    web_pid, web_name = load_csv_index(WEB_SEARCH_CSV)
    print(f"  {len(web_pid)} po place_id, {len(web_name)} po imenu+naslovu")

    print(f"Berem {COMPANYWALL_CSV} ...")
    cw_pid, cw_name = load_csv_index(COMPANYWALL_CSV)
    print(f"  {len(cw_pid)} po place_id, {len(cw_name)} po imenu+naslovu")

    print(f"Nalagam {LEADS_JSON} ...")
    with open(LEADS_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    leads = data.get("leads", [])
    print(f"  {len(leads)} leadov v dashboardu")

    from_site = 0
    from_web = 0
    from_companywall = 0

    for lead in leads:
        # Ze ima e-mail (npr. rocno vnesen prej) -> ne prepisuj
        if (lead.get("email") or "").strip():
            continue

        site_row = lookup(enr_pid, enr_name, lead)
        if site_row and (site_row.get("email") or "").strip():
            lead["email"] = site_row["email"]
            lead["email_source"] = site_row.get("email_source", "")
            from_site += 1
            continue

        web_row = lookup(web_pid, web_name, lead)
        if web_row and (web_row.get("web_email") or "").strip():
            lead["email"] = web_row["web_email"]
            lead["email_source"] = web_row.get("web_email_method", "splet")
            from_web += 1
            continue

        cw_row = lookup(cw_pid, cw_name, lead)
        if cw_row and (cw_row.get("web_email") or "").strip():
            lead["email"] = cw_row["web_email"]
            lead["email_source"] = cw_row.get("web_email_method", "companywall")
            from_companywall += 1

    # Varnostna kopija pred prepisom
    backup_path = LEADS_JSON + ".bak"
    shutil.copy2(LEADS_JSON, backup_path)
    print(f"\nVarnostna kopija: {backup_path}")

    with open(LEADS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_with_email = sum(1 for l in leads if (l.get("email") or "").strip())

    print(f"\n=== KONČANO ===")
    print(f"Novih e-mailov iz lastne strani: {from_site}")
    print(f"Novih e-mailov iz spletnega iskanja: {from_web}")
    print(f"Novih e-mailov iz companywall.si: {from_companywall}")
    print(f"Skupaj leadov z e-mailom zdaj: {total_with_email} / {len(leads)}")
    print(f"Posodobljeno: {LEADS_JSON}")
    print(f"\nOpomba: to je SAMO lokalna datoteka. Za objavo na grafeio-lead.netlify.app")
    print(f"je treba se commitati in pushati v lead-dashboard repo (locen korak).")


if __name__ == "__main__":
    main()

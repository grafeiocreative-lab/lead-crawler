"""Wrapper za diagnose.py z resume podporo in sproti pisanjem."""
import csv
import os
import time
from diagnose import diagnose_website
from config import OUTPUT_DIR, HTTP_TIMEOUT

INPUT = os.path.join(OUTPUT_DIR, "businesses_all.csv")
OUTPUT = os.path.join(OUTPUT_DIR, "diagnostics.csv")

FIELDNAMES = [
    "name", "category", "location", "address", "phone",
    "google_rating", "google_reviews_count", "url", "reachable",
    "has_website", "status_code", "load_time_s", "has_ssl",
    "is_mobile_friendly", "has_title", "title", "has_meta_description",
    "has_h1", "has_favicon", "copyright_year", "images_without_alt",
    "social_count", "broken_links_count", "has_robots", "has_sitemap",
    "uses_wordpress", "generator", "errors",
]

# Nalozi podjetja
businesses = []
with open(INPUT, "r", encoding="utf-8") as f:
    businesses = list(csv.DictReader(f))
total = len(businesses)

# Resume: preberi ze narejene
done = set()
if os.path.exists(OUTPUT) and os.path.getsize(OUTPUT) > 100:
    with open(OUTPUT, "r", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            done.add(row.get("name", ""))
    print(f"RESUME: {len(done)} ze narejenih, nadaljujem...\n")
    mode = "a"
else:
    mode = "w"

out = open(OUTPUT, mode, newline="", encoding="utf-8")
writer = csv.DictWriter(out, fieldnames=FIELDNAMES)
if mode == "w":
    writer.writeheader()

count = len(done)
try:
    for i, biz in enumerate(businesses):
        name = biz.get("name", "?")
        if name in done:
            continue
        website = biz.get("website", "").strip()
        count += 1
        if not website:
            row = {k: "" for k in FIELDNAMES}
            row["name"] = name
            row["category"] = biz.get("category", "")
            row["location"] = biz.get("location", "")
            row["address"] = biz.get("address", "")
            row["phone"] = biz.get("phone", "")
            row["google_rating"] = biz.get("google_rating", "")
            row["google_reviews_count"] = biz.get("google_reviews_count", "")
            row["has_website"] = False
            row["reachable"] = False
            row["errors"] = "Nima spletne strani"
            writer.writerow(row)
            out.flush()
            print(f"  [{count}/{total}] {name}: NIMA STRANI *")
            continue
        print(f"  [{count}/{total}] {name}: {website}")
        try:
            diag = diagnose_website(website)
        except Exception as e:
            diag = {"url": website, "errors": str(e), "reachable": False}
        diag["name"] = name
        diag["category"] = biz.get("category", "")
        diag["location"] = biz.get("location", "")
        diag["address"] = biz.get("address", "")
        diag["phone"] = biz.get("phone", "")
        diag["google_rating"] = biz.get("google_rating", "")
        diag["google_reviews_count"] = biz.get("google_reviews_count", "")
        diag["has_website"] = True
        row = {k: diag.get(k, "") for k in FIELDNAMES}
        writer.writerow(row)
        out.flush()
        time.sleep(0.1)
except KeyboardInterrupt:
    print(f"\n\nPrekinjeno. Shranjenih: {count}")
finally:
    out.close()
    print(f"\nKoncano. Shranjenih {count} v {OUTPUT}")

"""
GRAFEIO Lead Crawler — Diagnostika spletnih strani
====================================================
Za vsako podjetje preveri stanje spletne strani.
"""

import csv
import os
import re
import ssl
import socket
import time
from datetime import datetime
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from config import HTTP_TIMEOUT, MAX_INTERNAL_LINKS_CHECK, OUTPUT_DIR

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

SOCIAL_DOMAINS = {
    "facebook.com": "facebook",
    "fb.com": "facebook",
    "instagram.com": "instagram",
    "linkedin.com": "linkedin",
    "twitter.com": "twitter",
    "x.com": "twitter",
    "youtube.com": "youtube",
    "tiktok.com": "tiktok",
}

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")

# Domene in lokalni deli, ki so skoraj vedno placeholderji/tracking, ne pravi kontakt
EMAIL_JUNK_DOMAINS = {
    "sentry.io", "wixpress.com", "example.com", "domain.com", "email.com",
    "yourdomain.com", "yoursite.com", "w3.org", "schema.org", "godaddy.com",
    "godaddy.co", "wordpress.org", "wordpress.com", "gmpg.org", "cloudflare.com",
    "google.com", "googleapis.com", "gstatic.com", "sentry-next.io",
}
EMAIL_JUNK_LOCALPARTS = {
    "test", "example", "yourname", "name", "user", "someone", "no-reply",
    "noreply",
}

# Poti, kjer je e-mail najpogosteje objavljen, ce ga ni na naslovnici
CONTACT_PATHS = ["/kontakt", "/kontakti", "/contact", "/contact-us", "/o-nas", "/about"]


def _is_junk_email(email):
    """Preveri ali je e-mail ocitno placeholder/tracking, ne pravi kontakt."""
    email = email.lower()
    local, _, domain = email.partition("@")
    if domain in EMAIL_JUNK_DOMAINS:
        return True
    if local in EMAIL_JUNK_LOCALPARTS:
        return True
    # Slike z density descriptorjem ("logo@2x.png") ujete kot lazen email
    if re.search(r"\.(png|jpe?g|gif|svg|webp|ico)$", domain):
        return True
    return False


def extract_emails(soup):
    """Poisce e-mail naslove na strani: najprej mailto: linki, nato prosto besedilo."""
    found = []

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.lower().startswith("mailto:"):
            addr = href[7:].split("?")[0].strip()
            if addr:
                found.append(addr)

    text = soup.get_text(" ", strip=True)
    found.extend(EMAIL_REGEX.findall(text))

    seen = set()
    clean = []
    for e in found:
        e = e.strip().strip(".,;:").lower()
        if not e or e in seen or _is_junk_email(e):
            continue
        seen.add(e)
        clean.append(e)

    return clean


def find_contact_page_url(soup, base_url):
    """Poisce interno povezavo na kontakt/o-nas stran, ce obstaja."""
    base_parsed = urlparse(base_url)
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"]
        if href.lower().startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        if parsed.netloc != base_parsed.netloc:
            continue
        path = parsed.path.lower().rstrip("/")
        if any(path == p or path.endswith(p) for p in CONTACT_PATHS):
            return full_url
    return None


def check_ssl(domain):
    """Preveri ali ima domena veljaven SSL certifikat."""
    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=domain) as s:
            s.settimeout(HTTP_TIMEOUT)
            s.connect((domain, 443))
            cert = s.getpeercert()
            expiry = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
            return {
                "has_ssl": True,
                "ssl_expiry": expiry.isoformat(),
                "ssl_days_left": (expiry - datetime.now()).days,
            }
    except Exception:
        return {"has_ssl": False, "ssl_expiry": "", "ssl_days_left": 0}


def check_robots_sitemap(base_url):
    """Preveri ali obstajata robots.txt in sitemap.xml."""
    results = {"has_robots": False, "has_sitemap": False}

    for path, key in [("/robots.txt", "has_robots"), ("/sitemap.xml", "has_sitemap")]:
        try:
            resp = requests.get(
                urljoin(base_url, path), headers=HEADERS, timeout=HTTP_TIMEOUT
            )
            results[key] = resp.status_code == 200 and len(resp.text) > 10
        except Exception:
            pass

    return results


def check_broken_links(soup, base_url, max_check=MAX_INTERNAL_LINKS_CHECK):
    """Preveri prvih N internih linkov ali so broken."""
    broken = []
    checked = 0

    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "")

        # Preskoci eksterne, mailto, tel, anchor linke
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue

        # Sestavi polni URL
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)
        base_parsed = urlparse(base_url)

        # Samo interni linki
        if parsed.netloc != base_parsed.netloc:
            continue

        if checked >= max_check:
            break

        try:
            resp = requests.head(
                full_url, headers=HEADERS, timeout=HTTP_TIMEOUT, allow_redirects=True
            )
            if resp.status_code >= 400:
                broken.append(full_url)
        except Exception:
            broken.append(full_url)

        checked += 1

    return broken


def extract_copyright_year(soup):
    """Poisce leto v copyright besedilu."""
    footer = soup.find("footer") or soup
    text = footer.get_text()
    # Isci vzorce kot "© 2023", "copyright 2021", "2024"
    matches = re.findall(r"(?:©|\bcopyright\b)\s*(\d{4})", text, re.IGNORECASE)
    if matches:
        return max(int(y) for y in matches)

    # Fallback: isci katerokoli letnico v footerju
    if soup.find("footer"):
        footer_text = soup.find("footer").get_text()
        years = re.findall(r"\b(20[12]\d)\b", footer_text)
        if years:
            return max(int(y) for y in years)

    return None


def extract_social_links(soup):
    """Poisce linke na socialna omrezja."""
    found = {}
    for a_tag in soup.find_all("a", href=True):
        href = a_tag.get("href", "").lower()
        for domain, platform in SOCIAL_DOMAINS.items():
            if domain in href and platform not in found:
                found[platform] = a_tag.get("href", "")
    return found


def diagnose_website(url):
    """Izvede diagnostiko ene spletne strani. Vrne slovar z rezultati."""

    result = {
        "url": url,
        "reachable": False,
        "status_code": None,
        "load_time_s": None,
        "has_ssl": False,
        "ssl_expiry": "",
        "ssl_days_left": 0,
        "is_mobile_friendly": False,
        "has_title": False,
        "title": "",
        "has_meta_description": False,
        "meta_description": "",
        "has_h1": False,
        "has_favicon": False,
        "copyright_year": None,
        "images_total": 0,
        "images_without_alt": 0,
        "social_links": "",
        "social_count": 0,
        "broken_links": "",
        "broken_links_count": 0,
        "has_robots": False,
        "has_sitemap": False,
        "uses_wordpress": False,
        "uses_wix": False,
        "uses_squarespace": False,
        "generator": "",
        "email": "",
        "email_source": "",
        "errors": "",
    }

    # Normaliziraj URL
    if not url.startswith("http"):
        url = "https://" + url
    result["url"] = url

    parsed = urlparse(url)
    domain = parsed.netloc or parsed.path.split("/")[0]

    # 1. SSL
    ssl_info = check_ssl(domain)
    result.update(ssl_info)

    # 2. HTTP zahteva
    try:
        start = time.time()
        resp = requests.get(
            url,
            headers=HEADERS,
            timeout=HTTP_TIMEOUT,
            allow_redirects=True,
        )
        load_time = round(time.time() - start, 2)

        result["reachable"] = True
        result["status_code"] = resp.status_code
        result["load_time_s"] = load_time

        # Sledi preusmeritvam
        if resp.url != url:
            result["url"] = resp.url

    except requests.ConnectionError:
        result["errors"] = "Stran ni dosegljiva (ConnectionError)"
        return result
    except requests.Timeout:
        result["errors"] = "Stran se ne odzove v roku (Timeout)"
        return result
    except Exception as e:
        result["errors"] = f"Napaka: {str(e)[:100]}"
        return result

    if resp.status_code >= 400:
        result["errors"] = f"HTTP {resp.status_code}"
        return result

    # 3. HTML analiza
    soup = BeautifulSoup(resp.text, "lxml")

    # Title
    title_tag = soup.find("title")
    if title_tag and title_tag.string:
        result["has_title"] = True
        result["title"] = title_tag.string.strip()[:200]

    # Meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and meta_desc.get("content"):
        result["has_meta_description"] = True
        result["meta_description"] = meta_desc["content"].strip()[:300]

    # Mobile: viewport meta tag
    viewport = soup.find("meta", attrs={"name": "viewport"})
    result["is_mobile_friendly"] = viewport is not None

    # H1
    result["has_h1"] = soup.find("h1") is not None

    # Favicon
    favicon = (
        soup.find("link", rel=re.compile(r"icon", re.I))
        or soup.find("link", rel="shortcut icon")
    )
    result["has_favicon"] = favicon is not None

    # Copyright leto
    result["copyright_year"] = extract_copyright_year(soup)

    # Slike brez alt
    images = soup.find_all("img")
    result["images_total"] = len(images)
    result["images_without_alt"] = sum(
        1 for img in images if not img.get("alt", "").strip()
    )

    # Socialni linki
    socials = extract_social_links(soup)
    result["social_links"] = ", ".join(f"{k}: {v}" for k, v in socials.items())
    result["social_count"] = len(socials)

    # E-mail: najprej na naslovnici
    emails = extract_emails(soup)
    if emails:
        result["email"] = "; ".join(emails[:3])
        result["email_source"] = "naslovnica"
    else:
        # Ce ni na naslovnici, poskusi kontakt/o-nas stran (1 dodatna zahteva)
        contact_url = find_contact_page_url(soup, result["url"])
        if contact_url:
            try:
                c_resp = requests.get(
                    contact_url, headers=HEADERS, timeout=HTTP_TIMEOUT
                )
                if c_resp.status_code == 200:
                    c_soup = BeautifulSoup(c_resp.text, "lxml")
                    c_emails = extract_emails(c_soup)
                    if c_emails:
                        result["email"] = "; ".join(c_emails[:3])
                        result["email_source"] = "kontakt stran"
            except Exception:
                pass

    # CMS/generator detekcija
    generator = soup.find("meta", attrs={"name": "generator"})
    if generator:
        gen_content = generator.get("content", "").lower()
        result["generator"] = generator.get("content", "")[:100]
        result["uses_wordpress"] = "wordpress" in gen_content

    html_lower = resp.text[:5000].lower()
    result["uses_wix"] = "wix.com" in html_lower or "wixsite" in html_lower
    result["uses_squarespace"] = "squarespace" in html_lower
    if "wp-content" in resp.text or "wp-includes" in resp.text:
        result["uses_wordpress"] = True

    # 4. Broken links
    broken = check_broken_links(soup, result["url"])
    result["broken_links"] = "; ".join(broken)
    result["broken_links_count"] = len(broken)

    # 5. robots.txt in sitemap.xml
    base = f"{parsed.scheme}://{domain}"
    rs = check_robots_sitemap(base)
    result.update(rs)

    return result


def load_businesses(filepath):
    """Nalozi podjetja iz CSV (maps ali bizi output)."""
    businesses = []
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            businesses.append(dict(row))
    return businesses


def run_diagnostics(businesses):
    """Izvede diagnostiko za vsa podjetja s spletno stranjo."""
    results = []

    total = len(businesses)
    with_site = sum(1 for b in businesses if b.get("website"))
    without_site = total - with_site

    print(f"\n  Skupaj podjetij: {total}")
    print(f"  S spletno stranjo: {with_site}")
    print(f"  BREZ spletne strani: {without_site} (potencialni leadi!)\n")

    for i, biz in enumerate(businesses):
        name = biz.get("name", "?")
        website = biz.get("website", "").strip()

        if not website:
            # Podjetje brez strani = hot lead
            results.append({
                "name": name,
                "category": biz.get("category", ""),
                "location": biz.get("location", ""),
                "address": biz.get("address", ""),
                "phone": biz.get("phone", ""),
                "google_rating": biz.get("google_rating", ""),
                "google_reviews_count": biz.get("google_reviews_count", ""),
                "url": "",
                "reachable": False,
                "has_website": False,
                "status_code": None,
                "load_time_s": None,
                "has_ssl": False,
                "is_mobile_friendly": False,
                "has_title": False,
                "title": "",
                "has_meta_description": False,
                "has_h1": False,
                "has_favicon": False,
                "copyright_year": None,
                "images_without_alt": 0,
                "social_count": 0,
                "broken_links_count": 0,
                "has_robots": False,
                "has_sitemap": False,
                "uses_wordpress": False,
                "generator": "",
                "email": "",
                "email_source": "",
                "errors": "Nima spletne strani",
            })
            print(f"  [{i+1}/{total}] {name}: NIMA STRANI ★")
            continue

        print(f"  [{i+1}/{total}] {name}: {website}")

        diag = diagnose_website(website)
        diag["name"] = name
        diag["category"] = biz.get("category", "")
        diag["location"] = biz.get("location", "")
        diag["address"] = biz.get("address", "")
        diag["phone"] = biz.get("phone", "")
        diag["google_rating"] = biz.get("google_rating", "")
        diag["google_reviews_count"] = biz.get("google_reviews_count", "")
        diag["has_website"] = True
        results.append(diag)

        # Spoštuj rate limit
        time.sleep(0.5)

    return results


def save_diagnostics(results, filename="diagnostics.csv"):
    """Shrani diagnostiko v CSV."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    if not results:
        print("Ni rezultatov za shranjevanje.")
        return

    fieldnames = results[0].keys()
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n  Shranjeno {len(results)} diagnostik v {filepath}")
    return filepath


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Uporaba: python diagnose.py <businesses.csv>")
        sys.exit(1)

    filepath = sys.argv[1]
    print(f"=== Diagnostika spletnih strani ===")
    print(f"Vhod: {filepath}")

    businesses = load_businesses(filepath)
    results = run_diagnostics(businesses)
    save_diagnostics(results)

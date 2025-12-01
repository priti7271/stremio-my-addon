import requests
from bs4 import BeautifulSoup
import re
from collections import OrderedDict

URL = "https://www.imdb.com/chart/top/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

def fetch(url):
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    return resp.text

def dedupe_preserve_order(seq):
    temp = OrderedDict()
    for item in seq:
        temp[item["id"]] = item   # dedupe by unique IMDb ID
    return list(temp.values())

def extract_by_selectors(soup):
    results = []

    # ========== 1) NEW IMDB LAYOUT ==========
    li_items = soup.find_all("li", class_="ipc-metadata-list-summary-item")
    if li_items:
        for li in li_items:
            a = li.find("a", href=True)
            if not a:
                continue

            name_tag = a.find(["h3", "span"])
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            href = a.get("href", "")

            m = re.search(r"/title/(tt\d+)/", href)
            if not m:
                continue
            imdb_id = m.group(1)

            results.append({"name": name, "id": imdb_id})

        if results:
            return dedupe_preserve_order(results), "new_layout"

    # ========== 2) OLD IMDB LAYOUT ==========
    tds = soup.select("td.titleColumn a")
    if tds:
        for t in tds:
            name = t.get_text(strip=True)
            href = t.get("href", "")
            
            m = re.search(r"/title/(tt\d+)/", href)
            if not m:
                continue
            imdb_id = m.group(1)

            results.append({"name": name, "id": imdb_id})

        if results:
            return dedupe_preserve_order(results), "old_layout"

    # ========== 3) GENERIC FALLBACK ==========
    anchors = soup.find_all("a", href=True)
    for a in anchors:
        href = a["href"]
        m = re.search(r"^/title/(tt\d+)", href)
        if m:
            imdb_id = m.group(1)
            text = a.get_text(strip=True)
            if text:
                results.append({"name": text, "id": imdb_id})

    return dedupe_preserve_order(results), "generic"


# ============================
# 🔧 FIXED PART (ONLY FIXED CODE)
# ============================

def slugify(name):
    # Remove apostrophes only (the broken part)
    name = name.replace("'", "")
    # Replace spaces and special chars with hyphens
    name = re.sub(r"[^a-zA-Z0-9]+", "-", name)
    # Lowercase
    name = name.lower()
    # Trim hyphens
    return name.strip("-")


# ============================
# MAIN (Unchanged)
# ============================

def get_imdb_catalog():
    html = fetch(URL)
    soup = BeautifulSoup(html, "html.parser")

    movies, method = extract_by_selectors(soup)

    catalog = []
    for movie in movies:
        movie_slug = slugify(movie['name'])

        
        meta = {
            "id": movie['id'],  # "tt0111161"
            "type": "movie",
            "name": movie['name'],
            "poster": f"https://img.omdbapi.com/?i={movie['id']}&h=600&apikey=YOUR_OMDB_KEY",
            "description": f"IMDB Top Rated: {movie['name']}",
            "links": [
                {"url": f"https://www.strem.io/s/movie/{movie_slug}-{movie['id'][2:]}"}
            ]
        }
        catalog.append(meta)

    return catalog
def main():
    catalog = get_imdb_catalog()
    for movie in catalog:
        print(f"{movie['name']} ({movie['id']}) - Link: {movie['links'][0]['url']}")

if __name__ == "__main__":
    main()

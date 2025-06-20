import json

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://harrypotter.fandom.com"
SPELLS_URL = f"{BASE_URL}/wiki/List_of_spells"
LOCAL_FILE = "cached_spells_page.html"
OUTPUT_JSON = "spells.json"


def download_html(url=SPELLS_URL, filename=LOCAL_FILE):
    response = requests.get(url)
    response.raise_for_status()
    with open(filename, "w", encoding="utf-8") as f:
        f.write(response.text)
    print(f"HTML saved to {filename}")


def parse_html(filename=LOCAL_FILE):
    with open(filename, encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    spells = []
    for span in soup.select("span.mw-headline"):
        if span.a:
            name = span.a.text.strip()
            description = span.a["title"]
            link = f"{BASE_URL}{span.a['href']}"
            spells.append({"name": name, "description": description, "link": link})

    return spells


def save_to_json(data, filename=OUTPUT_JSON):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Saved {len(data)} spells to {filename}")


if __name__ == "__main__":
    download_html()
    spells = parse_html()
    save_to_json(spells)

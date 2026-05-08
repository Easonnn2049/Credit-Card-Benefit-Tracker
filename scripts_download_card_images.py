from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urljoin

import pandas as pd
import requests


DATA_DIR = Path("data")
IMAGE_DIR = DATA_DIR / "card_images"
CARDS_CSV = DATA_DIR / "cards.csv"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

PAGE_OVERRIDES = {
    "chase_sapphire_preferred_p1": [
        "https://creditcards.chase.com/rewards-credit-cards/sapphire/preferred",
        "https://www.chase.com/sapphire-cards/personal/preferred",
    ],
    "chase_sapphire_reserve_p1": [
        "https://creditcards.chase.com/rewards-credit-cards/chase-sapphire-reserve",
        "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
        "https://www.chase.com/sapphire-cards/personal/reserve",
    ],
    "chase_sapphire_reserve_p2": [
        "https://creditcards.chase.com/rewards-credit-cards/chase-sapphire-reserve",
        "https://creditcards.chase.com/rewards-credit-cards/sapphire/reserve",
        "https://www.chase.com/sapphire-cards/personal/reserve",
    ],
    "chase_united_quest_p1": [
        "https://creditcards.chase.com/travel-credit-cards/united/united-quest",
        "https://www.chase.com/personal/credit-cards/united/united-quest-card",
    ],
    "chase_hyatt_p1": [
        "https://creditcards.chase.com/travel-credit-cards/world-of-hyatt-credit-card",
        "https://creditcards.chase.com/credit-cards/hyatt",
    ],
    "amex_hilton_p1": [
        "https://www.hilton.com/en/hilton-honors/credit-cards/",
        "https://www.americanexpress.com/en-us/account/get-started/hiltonsurpass",
        "https://www.americanexpress.com/en-us/account/get-started/hiltonsurpass/uncover-your-benefits",
    ],
}

KEYWORDS = {
    "amex_gold": ["gold", "card"],
    "amex_platinum": ["platinum", "card"],
    "chase_sapphire_preferred": ["sapphire", "preferred", "card"],
    "chase_sapphire_reserve": ["sapphire", "reserve", "card"],
    "chase_united_quest": ["united", "quest", "card"],
    "chase_marriott_boundless": ["marriott", "boundless", "card"],
    "chase_hyatt": ["hyatt", "card"],
    "amex_hilton": ["hilton", "card"],
    "usbank_altitude_reserve": ["altitude", "reserve", "card"],
}


def card_family(card_id: str) -> str:
    for family in KEYWORDS:
        if card_id.startswith(family):
            return family
    return card_id


def image_extension(url: str, content_type: str = "") -> str:
    lowered = url.lower().split("?")[0]
    for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg"]:
        if lowered.endswith(ext):
            return ext
    if "svg" in content_type:
        return ".svg"
    if "webp" in content_type:
        return ".webp"
    if "jpeg" in content_type or "jpg" in content_type:
        return ".jpg"
    return ".png"


def extract_image_candidates(html: str, base_url: str) -> list[str]:
    urls = set()
    patterns = [
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
        r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
        r'<img[^>]+src=["\']([^"\']+)["\']',
        r'srcSet=["\']([^"\']+)["\']',
        r'srcset=["\']([^"\']+)["\']',
        r'["\']([^"\']+\.(?:png|jpg|jpeg|webp)(?:\?[^"\']*)?)["\']',
    ]
    for pattern in patterns:
        for match in re.findall(pattern, html, flags=re.IGNORECASE):
            parts = [match]
            if "," in match and " " in match:
                parts = [item.strip().split(" ")[0] for item in match.split(",")]
            for part in parts:
                if part.startswith("data:"):
                    continue
                urls.add(urljoin(base_url, part.replace("\\/", "/")))
    return list(urls)


def score_url(url: str, family: str) -> int:
    lowered = url.lower()
    score = 0
    for keyword in KEYWORDS.get(family, []):
        if keyword in lowered:
            score += 10
    for good in ["card", "product", "hero", "credit-card", "cc"]:
        if good in lowered:
            score += 3
    for bad in ["logo", "icon", "badge", "award", "hotel", "apple", "lyft", "uber", "banner", "background"]:
        if bad in lowered:
            score -= 8
    return score


def download_best_image(card_id: str, page_urls: list[str]) -> str:
    family = card_family(card_id)
    candidates = []
    for page_url in page_urls:
        try:
            response = requests.get(page_url, headers=HEADERS, timeout=20)
            response.raise_for_status()
        except Exception as exc:
            print(f"{card_id}: page failed {page_url}: {exc}")
            continue
        for image_url in extract_image_candidates(response.text, page_url):
            candidates.append((score_url(image_url, family), image_url))

    candidates.sort(reverse=True)
    for score, image_url in candidates[:25]:
        if score < 6:
            continue
        try:
            image = requests.get(image_url, headers=HEADERS, timeout=20)
            image.raise_for_status()
            content_type = image.headers.get("content-type", "")
            if "image" not in content_type.lower() and not re.search(r"\.(png|jpg|jpeg|webp|svg)(\?|$)", image_url, re.I):
                continue
            if len(image.content) < 5000:
                continue
            extension = image_extension(image_url, content_type)
            path = IMAGE_DIR / f"{card_id}{extension}"
            path.write_bytes(image.content)
            return f"saved {path.name} from {image_url}"
        except Exception as exc:
            print(f"{card_id}: image failed {image_url}: {exc}")
    return "no suitable image found"


def main() -> None:
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    cards = pd.read_csv(CARDS_CSV)
    for _, card in cards.iterrows():
        card_id = str(card["card_id"])
        page_urls = PAGE_OVERRIDES.get(card_id, [])
        source_url = str(card.get("source_url", "") or "")
        if source_url.startswith("http"):
            page_urls.append(source_url)
        page_urls = list(dict.fromkeys(page_urls))
        print(card_id, download_best_image(card_id, page_urls))


if __name__ == "__main__":
    main()

import json
import os
import re
import sys

from bs4 import BeautifulSoup

from schema import UnifiedDocument

MISSING_PRICE_TOKENS = {"n/a", "liên hệ", "lien he", ""}


def _parse_price_to_vnd(price_text):
    normalized = price_text.strip().lower()
    if normalized in MISSING_PRICE_TOKENS:
        return None

    numeric_text = re.sub(r"[^0-9.-]", "", price_text)
    if not numeric_text:
        return None
    return float(numeric_text)


def _parse_inventory(raw_inventory):
    try:
        return int(raw_inventory)
    except ValueError:
        return None


def parse_html_catalog(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f, "html.parser")

    catalog = soup.find("table", id="main-catalog")
    if catalog is None:
        return []

    rows = catalog.select("tbody tr")
    documents = []
    original_file = os.path.basename(file_path)

    for row in rows:
        cells = [cell.get_text(strip=True) for cell in row.find_all("td")]
        if len(cells) != 6:
            continue

        product_code, product_name, category, raw_price, raw_inventory, rating = cells
        price_vnd = _parse_price_to_vnd(raw_price)
        inventory = _parse_inventory(raw_inventory)

        content = (
            f"Catalog item {product_code}: {product_name} belongs to category {category}. "
            f"Listed price is {price_vnd if price_vnd is not None else 'not available'} VND, "
            f"inventory is {inventory if inventory is not None else 'unknown'}, and rating is {rating}."
        )

        document = UnifiedDocument(
            document_id=f"html-product-{product_code.lower()}",
            content=content,
            source_type="HTML",
            author="Unknown",
            timestamp=None,
            source_metadata={
                "original_file": original_file,
                "product_code": product_code,
                "product_name": product_name,
                "category": category,
                "raw_price": raw_price,
                "price_vnd": price_vnd,
                "inventory": inventory,
                "rating": rating,
            },
        )
        documents.append(document.dict())

    return documents


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_html = os.path.join(os.path.dirname(current_dir), "raw_data", "product_catalog.html")

    print("--- Testing HTML Extraction ---")
    result = parse_html_catalog(test_html)
    if result:
        print("\nSuccess! Extracted Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\nExtraction failed.")

import json
import os
import re
import sys

import pandas as pd

from schema import UnifiedDocument

MISSING_PRICE_TOKENS = {"n/a", "null", "liên hệ", "lien he", ""}
DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%B %dth %Y",
    "%d-%m-%Y",
    "%Y/%m/%d",
    "%d %b %Y",
    "%B %dnd %Y",
    "%B %drd %Y",
    "%B %dst %Y",
]


def _normalize_price(raw_price):
    if pd.isna(raw_price):
        return None, None

    price_text = str(raw_price).strip()
    normalized = price_text.lower()
    if normalized in MISSING_PRICE_TOKENS:
        return None, None

    if normalized.startswith("$"):
        try:
            return float(normalized.replace("$", "").replace(",", "")), None
        except ValueError:
            return None, f"Unable to parse USD price: {price_text}"

    numeric_text = re.sub(r"[^0-9.-]", "", price_text)
    if not numeric_text:
        return None, f"Unable to parse price: {price_text}"

    try:
        return float(numeric_text), None
    except ValueError:
        return None, f"Unable to parse price: {price_text}"


def _normalize_date(raw_date):
    if pd.isna(raw_date):
        return None

    date_text = str(raw_date).strip()
    for fmt in DATE_FORMATS:
        try:
            return pd.to_datetime(date_text, format=fmt, errors="raise").strftime("%Y-%m-%d")
        except (ValueError, TypeError):
            continue

    parsed = pd.to_datetime(date_text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        return None
    return parsed.strftime("%Y-%m-%d")


def _normalize_stock(raw_stock):
    if pd.isna(raw_stock) or str(raw_stock).strip() == "":
        return None
    try:
        return int(float(raw_stock))
    except ValueError:
        return None


def _clean_optional_value(value):
    return None if pd.isna(value) else value


def process_sales_csv(file_path):
    df = pd.read_csv(file_path)
    df = df.drop_duplicates(subset=["id"], keep="first")

    documents = []
    original_file = os.path.basename(file_path)

    for row in df.to_dict(orient="records"):
        price_value, price_error = _normalize_price(row.get("price"))
        normalized_date = _normalize_date(row.get("date_of_sale"))
        stock_quantity = _normalize_stock(row.get("stock_quantity"))
        currency = row.get("currency", "Unknown")
        raw_price = _clean_optional_value(row.get("price"))

        content = (
            f"Sale record {row['id']}: Product {row['product_name']} in category {row['category']} "
            f"sold on {normalized_date or 'unknown date'} for {price_value if price_value is not None else 'unknown price'} "
            f"{currency} by seller {row['seller_id']}. Stock quantity recorded: "
            f"{stock_quantity if stock_quantity is not None else 'unknown'}."
        )

        metadata = {
            "original_file": original_file,
            "record_id": str(row["id"]),
            "product_name": row.get("product_name"),
            "category": row.get("category"),
            "raw_price": raw_price,
            "normalized_price": price_value,
            "currency": currency,
            "normalized_date_of_sale": normalized_date,
            "seller_id": row.get("seller_id"),
            "stock_quantity": stock_quantity,
        }
        if price_error:
            metadata["price_parse_error"] = price_error

        document = UnifiedDocument(
            document_id=f"csv-sale-{row['id']}",
            content=content,
            source_type="CSV",
            author="Unknown",
            timestamp=None,
            source_metadata=metadata,
        )
        documents.append(document.dict())

    return documents


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_csv = os.path.join(os.path.dirname(current_dir), "raw_data", "sales_records.csv")

    print("--- Testing CSV Extraction ---")
    result = process_sales_csv(test_csv)
    if result:
        print("\nSuccess! Extracted Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\nExtraction failed.")

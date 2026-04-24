import json
import os
import re
import sys

from schema import UnifiedDocument

NOISE_TOKENS = ["[Music starts]", "[Music ends]", "[inaudible]", "[Laughter]"]
VIETNAMESE_NUMBER_MAP = {
    "không": 0,
    "một": 1,
    "mốt": 1,
    "hai": 2,
    "ba": 3,
    "bốn": 4,
    "tư": 4,
    "năm": 5,
    "lăm": 5,
    "sáu": 6,
    "bảy": 7,
    "bẩy": 7,
    "tám": 8,
    "chín": 9,
}


def _parse_vietnamese_number_phrase(phrase):
    tokens = phrase.split()
    total = 0
    current = 0

    for token in tokens:
        if token in VIETNAMESE_NUMBER_MAP:
            current = VIETNAMESE_NUMBER_MAP[token]
        elif token == "mười":
            current = 10 if current == 0 else current * 10
        elif token == "trăm":
            current = max(current, 1) * 100
        elif token == "nghìn":
            total += max(current, 1) * 1000
            current = 0
        elif token == "triệu":
            total += max(current, 1) * 1000000
            current = 0
        else:
            return None

    total += current
    return total or None


def _parse_vietnamese_price(text):
    match = re.search(r"là\s+([a-zA-ZÀ-ỹ\s]+?)\s+vnd", text.lower())
    if not match:
        return None
    phrase = " ".join(match.group(1).split())
    return _parse_vietnamese_number_phrase(phrase)


def clean_transcript(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read()

    cleaned_text = text
    removed_tokens = []
    for token in NOISE_TOKENS:
        if token in cleaned_text:
            removed_tokens.append(token)
            cleaned_text = cleaned_text.replace(token, "")

    cleaned_text = re.sub(r"\[\d{2}:\d{2}:\d{2}\]\s*", "", cleaned_text)
    cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
    cleaned_text = cleaned_text.replace(": :", ":")

    speakers = sorted(set(re.findall(r"\[Speaker\s+\d+\]", text)))
    spoken_price = _parse_vietnamese_price(cleaned_text)
    numeric_prices = [
        int(price.replace(",", ""))
        for price in re.findall(r"(\d{1,3}(?:,\d{3})+)\s*VND", text, flags=re.IGNORECASE)
    ]

    document = UnifiedDocument(
        document_id="transcript-doc-001",
        content=cleaned_text,
        source_type="Transcript",
        author="Unknown",
        timestamp=None,
        source_metadata={
            "original_file": os.path.basename(file_path),
            "speakers_found": speakers,
            "price_mentions": {
                "spoken_vietnamese_price": spoken_price,
                "numeric_vnd_prices": numeric_prices,
            },
            "price_vnd": spoken_price or (numeric_prices[0] if numeric_prices else None),
            "noise_tokens_removed": removed_tokens,
        },
    )
    return document.dict()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_transcript = os.path.join(os.path.dirname(current_dir), "raw_data", "demo_transcript.txt")

    print("--- Testing Transcript Extraction ---")
    result = clean_transcript(test_transcript)
    if result:
        print("\nSuccess! Extracted Data:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\nExtraction failed.")

#!/usr/bin/env python3

import argparse
import asyncio
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from eandb.clients.v2 import EandbV2AsyncClient


LANG_PREFERENCE = ["de", "en", "es", "fr", "it", "nl", "no", "ru"]


def read_token(script_dir: Path) -> str:
    token_file = script_dir / "token"
    if not token_file.exists():
        raise FileNotFoundError(f"Token file not found: {token_file}")

    token = token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError(f"Token file is empty: {token_file}")

    return token


def choose_localized_value(values) -> str | None:
    if not values:
        return None

    for lang in LANG_PREFERENCE:
        value = values.get(lang)
        if value:
            return value

    for value in values.values():
        if value:
            return value

    return None


def slugify_filename_part(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[\/\\:]+", "-", value)
    value = re.sub(r"[^a-z0-9._ -]+", "", value)
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    value = value.strip("-. ")
    return value or "unknown"


def yaml_escape(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def looks_like_corporate_name(name: str) -> bool:
    lowered = name.lower()
    markers = [
        "gmbh", "ag", "kg", "ug", "llc", "ltd", "limited", "inc", "corp",
        "corporation", "company", "co.", "s.a.", "sa", "bv", "nv", "oy",
        "ab", "spa", "srl", "sas", "as", "gruppen", "group", "holding",
    ]
    return any(marker in lowered for marker in markers)


def infer_brand_from_title(title: str) -> str | None:
    words = title.split()
    if not words:
        return None

    brand_words = []
    for word in reversed(words):
        cleaned = re.sub(r"[^\w&'-]", "", word)
        if not cleaned:
            break
        if re.fullmatch(r"\d+(?:[.,]\d+)?(?:g|kg|ml|l|cl|oz)?", cleaned, re.IGNORECASE):
            break
        if cleaned[0].isupper():
            brand_words.append(cleaned)
        else:
            break

    if not brand_words:
        return None

    return " ".join(reversed(brand_words)).strip() or None


def extract_brand(product, raw_title: str | None) -> str:
    for brand in (product.relatedBrands or []):
        title = choose_localized_value(brand.titles)
        if title:
            return title.strip()

    manufacturer_title = None
    if product.manufacturer and getattr(product.manufacturer, "titles", None):
        manufacturer_title = choose_localized_value(product.manufacturer.titles)

    if manufacturer_title and not looks_like_corporate_name(manufacturer_title):
        return manufacturer_title.strip()

    inferred = infer_brand_from_title(raw_title or "")
    if inferred:
        return inferred

    if manufacturer_title:
        return manufacturer_title.strip()

    return "Unknown"


def strip_weight_tokens(text: str) -> str:
    text = re.sub(r"\b\d+(?:[.,]\d+)?\s?(?:g|kg|ml|l|cl|oz)\b", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s{2,}", " ", text).strip(" -_,")
    return text


def extract_product_type(product) -> str:
    categories = product.categories or []
    if categories:
        title = choose_localized_value(categories[0].titles)
        if title:
            return title.strip()
    return "Unknown"


def extract_product_name(raw_title: str | None, brand: str) -> str:
    if not raw_title:
        return "Unknown"

    name = raw_title.strip()
    if brand and name.lower().endswith(brand.lower()):
        name = name[:-len(brand)].strip(" -_,")

    name = strip_weight_tokens(name)
    return name or raw_title.strip()


def download_image(url: str, target_dir: Path, ean: str) -> str:
    target_dir.mkdir(parents=True, exist_ok=True)

    ext = Path(urlparse(url).path).suffix.lower() or ".jpg"
    filename = f"{ean}{ext}"
    target_path = target_dir / filename

    req = Request(url, headers={"User-Agent": "python-ean-lookup/1.0"})
    with urlopen(req) as response:
        target_path.write_bytes(response.read())

    return filename


def build_markdown(product_type: str, product_name: str, brand: str, image_filename: str) -> str:
    return (
        "---\n"
        f"product-type: {product_type}\n"
        f"brand: {brand}\n"
        f"product-name: {product_name}\n"
        f'image: "[[{image_filename}]]"\n'
        "rating: 0\n"
        "notes: \n"
        "---\n"
        "#product-ratings\n"
        '`="!"+this.image`\n'
    )

def write_markdown_file(output_dir: Path, brand: str, product_name: str, content: str) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{slugify_filename_part(brand)}-{slugify_filename_part(product_name)}.md"
    path = output_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


def validate_ean(ean: str) -> None:
    if not re.fullmatch(r"\d{8}|\d{13}|\d{14}", ean):
        raise ValueError("EAN must be 8, 13, or 14 digits.")


async def run(ean: str, output_dir: Path, script_dir: Path) -> int:
    validate_ean(ean)

    token = read_token(script_dir)
    client = EandbV2AsyncClient(jwt=token)

    response = await client.get_product(ean)

    if response.error:
        raise RuntimeError(f"API error {response.error.code}: {response.error.description}")

    if not response.product:
        raise RuntimeError("API returned no product data.")

    product = response.product

    raw_title = choose_localized_value(product.titles) or product.barcode
    brand = extract_brand(product, raw_title)
    product_type = extract_product_type(product)
    product_name = extract_product_name(raw_title, brand)

    if not product.images:
        raise RuntimeError("No product image available in API response.")

    image_url = product.images[0].url
    if not image_url:
        raise RuntimeError("First image entry has no URL.")

    image_filename = download_image(image_url, output_dir / "images", ean)
    markdown = build_markdown(product_type, product_name, brand, image_filename)
    markdown_path = write_markdown_file(output_dir, brand, product_name, markdown)

    print(f"Created: {markdown_path}")
    print(f"Image:   {output_dir / 'images' / image_filename}")
    print(f"Balance: {response.balance}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Look up an EAN and write a markdown file.")
    parser.add_argument("ean", help="EAN code, e.g. 8410076482563")
    parser.add_argument("-o", "--output-dir", default=".", help="Output directory")
    args = parser.parse_args()

    ean = args.ean.strip()
    output_dir = Path(args.output_dir).resolve()
    script_dir = Path(__file__).resolve().parent

    try:
        return asyncio.run(run(ean, output_dir, script_dir))
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
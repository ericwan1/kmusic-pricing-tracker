"""
Fixed schema definition for K-Pop pricing data.

This module defines the stable schema contract that all scrapers must
adhere to. No column renames or reordering allowed - this ensures
backward compatibility.
"""

from typing import Optional
import pandas as pd


# Fixed schema columns (order matters - do not change!)
SCHEMA_COLUMNS = [
    "item",  # string: Product name
    "url",  # string: Product URL
    "artist",  # string: Artist/group name (nullable)
    "discount_price",  # float: Discounted price if available (nullable)
    "price",  # float: Current price
    "sold_out",  # boolean: Availability status
    "ds",  # date: Date partition (YYYY-MM-DD)
]

# Schema types
SCHEMA_TYPES = {
    "item": str,
    "url": str,
    "artist": Optional[str],
    "discount_price": Optional[float],
    "price": float,
    "sold_out": bool,
    "ds": str,  # Stored as string 'YYYY-MM-DD', converted to date when needed
}


def validate_schema(df: pd.DataFrame) -> tuple[bool, list[str]]:
    """
    Validate that a DataFrame matches the fixed schema.

    Args:
        df: DataFrame to validate

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []

    # Check column names match exactly
    if list(df.columns) != SCHEMA_COLUMNS:
        msg = (
            f"Column mismatch. Expected: {SCHEMA_COLUMNS}, "
            f"Got: {list(df.columns)}"
        )
        errors.append(msg)
        return False, errors

    # Check required columns are not all null
    required_cols = ["item", "url", "price", "ds"]
    for col in required_cols:
        if df[col].isna().all():
            errors.append(f"Required column '{col}' is entirely null")

    # Check types
    if df["price"].dtype not in ["float64", "float32", "int64", "int32"]:
        msg = f"Column 'price' must be numeric, got {df['price'].dtype}"
        errors.append(msg)

    if df["sold_out"].dtype != "bool":
        # Try to convert
        try:
            df["sold_out"] = df["sold_out"].astype(bool)
        except Exception as e:
            errors.append(f"Cannot convert 'sold_out' to boolean: {e}")

    # Check ds format (should be YYYY-MM-DD)
    if df["ds"].dtype == "object":
        try:
            pd.to_datetime(df["ds"], format="%Y-%m-%d")
        except Exception:
            errors.append("Column 'ds' must be in YYYY-MM-DD format")

    is_valid = len(errors) == 0
    return is_valid, errors


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize DataFrame types to match schema requirements.

    Args:
        df: DataFrame to normalize

    Returns:
        Normalized DataFrame
    """
    df = df.copy()

    # Ensure price is numeric
    df["price"] = pd.to_numeric(df["price"], errors="coerce")

    # Ensure discount_price is numeric (nullable)
    if "discount_price" in df.columns:
        df["discount_price"] = pd.to_numeric(
            df["discount_price"], errors="coerce"
        )

    # Ensure sold_out is boolean
    if df["sold_out"].dtype != "bool":
        # Convert common representations
        df["sold_out"] = (
            df["sold_out"].astype(str).str.lower().isin(["true", "1", "yes"])
        )

    # Ensure ds is string in YYYY-MM-DD format
    if df["ds"].dtype != "object":
        df["ds"] = pd.to_datetime(df["ds"]).dt.strftime("%Y-%m-%d")
    else:
        # Validate format
        try:
            pd.to_datetime(df["ds"], format="%Y-%m-%d")
        except Exception:
            # Try to parse and reformat
            df["ds"] = pd.to_datetime(df["ds"]).dt.strftime("%Y-%m-%d")

    # Ensure string columns are strings
    df["item"] = df["item"].astype(str)
    df["url"] = df["url"].astype(str)
    if "artist" in df.columns:
        df["artist"] = (
            df["artist"].astype(str).replace("nan", None).replace("None", None)
        )

    return df


def create_empty_dataframe() -> pd.DataFrame:
    """
    Create an empty DataFrame with the correct schema.

    Returns:
        Empty DataFrame with schema columns
    """
    return pd.DataFrame(columns=SCHEMA_COLUMNS)


def map_to_schema(
    data: dict,
    vendor: str,
    ds: str,
    artist: Optional[str] = None,
    discount_price: Optional[float] = None,
) -> dict:
    """
    Map scraped data to fixed schema.

    Args:
        data: Dictionary with scraped data (may have different field names)
        vendor: Vendor identifier
        ds: Date string in YYYY-MM-DD format
        artist: Artist/group name (optional)
        discount_price: Discounted price (optional)

    Returns:
        Dictionary matching fixed schema
    """
    # Map common field name variations
    item = (
        data.get("item") or data.get("name") or
        data.get("product_name") or ""
    )
    url = (
        data.get("url") or data.get("link") or data.get("href") or ""
    )
    price = (
        data.get("price") or data.get("cost") or
        data.get("product_price") or 0.0
    )
    sold_out = data.get("sold_out") or data.get("is_sold_out") or False

    # Normalize price to float
    try:
        price = float(price)
    except (ValueError, TypeError):
        price = 0.0

    # Normalize sold_out to boolean
    if isinstance(sold_out, str):
        sold_out = sold_out.lower() in (
            "true", "1", "yes", "sold out", "unavailable"
        )
    else:
        sold_out = bool(sold_out)

    discount_price_val = None
    if discount_price is not None:
        discount_price_val = float(discount_price)

    return {
        "item": str(item),
        "url": str(url),
        "artist": str(artist) if artist else None,
        "discount_price": discount_price_val,
        "price": price,
        "sold_out": sold_out,
        "ds": str(ds),  # Ensure YYYY-MM-DD format
    }

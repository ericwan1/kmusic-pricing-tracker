"""
Data quality validation checks.
"""

from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def check_freshness(
    df: pd.DataFrame, expected_ds: str, max_days_old: int = 7
) -> tuple[bool, Optional[str]]:
    """
    Check that the latest ds is within expected window.

    Args:
        df: DataFrame with 'ds' column
        expected_ds: Expected date string (YYYY-MM-DD)
        max_days_old: Maximum days old data is acceptable

    Returns:
        tuple: (is_fresh, error_message)
    """
    if df.empty:
        return False, "DataFrame is empty"

    if "ds" not in df.columns:
        return False, "Missing 'ds' column"

    # Get latest ds
    latest_ds = pd.to_datetime(df["ds"]).max()
    expected_date = pd.to_datetime(expected_ds)

    days_diff = (expected_date - latest_ds).days

    if days_diff > max_days_old:
        return False, f"Data is {days_diff} days old (max: {max_days_old})"

    return True, None


def check_volume(
    df: pd.DataFrame,
    min_rows: int = 1,
    previous_count: Optional[int] = None,
    max_drop_percent: float = 50.0,
) -> tuple[bool, Optional[str]]:
    """
    Check that row count meets minimum and hasn't dropped unexpectedly.

    Args:
        df: DataFrame to check
        min_rows: Minimum expected rows
        previous_count: Previous run's row count (for drop check)
        max_drop_percent: Maximum acceptable drop percentage

    Returns:
        tuple: (is_valid, error_message)
    """
    row_count = len(df)

    # Check minimum
    if row_count < min_rows:
        return False, f"Row count ({row_count}) below minimum ({min_rows})"

    # Check drop from previous
    if previous_count is not None and previous_count > 0:
        drop_percent = ((previous_count - row_count) / previous_count) * 100

        if drop_percent > max_drop_percent:
            return False, (
                f"Row count dropped {drop_percent:.1f}% "
                f"({previous_count} -> {row_count}), "
                f"exceeds max drop of {max_drop_percent}%"
            )

    return True, None


def check_null_fields(
    df: pd.DataFrame, critical_fields: list[str] = None
) -> tuple[bool, list[str]]:
    """
    Check for null values in critical fields.

    Args:
        df: DataFrame to check
        critical_fields: List of fields that cannot be null

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    if critical_fields is None:
        critical_fields = ["item", "url", "artist", "price"]

    errors = []

    for field in critical_fields:
        if field not in df.columns:
            errors.append(f"Missing critical field: {field}")
            continue

        null_count = df[field].isna().sum()
        if null_count > 0:
            errors.append(
                f"Field '{field}' has {null_count} null values "
                f"({null_count/len(df)*100:.1f}%)"
            )

    is_valid = len(errors) == 0
    return is_valid, errors


def validate_data_quality(
    df: pd.DataFrame,
    expected_ds: str,
    min_rows: int = 1,
    previous_count: Optional[int] = None,
) -> tuple[bool, list[str]]:
    """
    Run all data quality checks.

    Args:
        df: DataFrame to validate
        expected_ds: Expected date string
        min_rows: Minimum expected rows
        previous_count: Previous run's row count

    Returns:
        tuple: (is_valid, list_of_errors)
    """
    errors = []

    # Freshness check
    is_fresh, freshness_error = check_freshness(df, expected_ds)
    if not is_fresh:
        errors.append(f"Freshness check failed: {freshness_error}")

    # Volume check
    is_valid_volume, volume_error = check_volume(df, min_rows, previous_count)
    if not is_valid_volume:
        errors.append(f"Volume check failed: {volume_error}")

    # Null check
    is_valid_nulls, null_errors = check_null_fields(df)
    if not is_valid_nulls:
        errors.extend([f"Null check failed: {e}" for e in null_errors])

    is_valid = len(errors) == 0
    return is_valid, errors

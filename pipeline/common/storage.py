"""
GCS storage utilities for raw data uploads.

Handles date-partitioned, append-only writes to Google Cloud Storage.
"""

import os
import json
from datetime import datetime
from typing import Optional
from google.cloud import storage
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def get_gcs_client() -> storage.Client:
    """Get GCS client (uses default credentials)."""
    return storage.Client()


def get_raw_data_path(
    vendor: str,
    ds: str,
    filename: Optional[str] = None
) -> str:
    """
    Generate GCS path for raw data (date-partitioned).

    Args:
        vendor: Vendor identifier (e.g., 'smglobalshop')
        ds: Date string in YYYY-MM-DD format
        filename: Optional filename (defaults to timestamp-based)
        vendor: Vendor identifier (e.g., 'smglobalshop')
        ds: Date string in YYYY-MM-DD format
        filename: Optional filename (defaults to timestamp-based)

    Returns:
        GCS path: raw/{vendor}/ds={ds}/{filename}
    """
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{vendor}_{timestamp}.jsonl"

    return f"raw/{vendor}/ds={ds}/{filename}"


def upload_dataframe_to_gcs(
    df: pd.DataFrame,
    bucket_name: str,
    gcs_path: str,
    check_exists: bool = True
) -> bool:
    """
    Upload DataFrame to GCS as JSONL (one record per line).

    Args:
        df: DataFrame to upload
        bucket_name: GCS bucket name
        gcs_path: GCS path (without gs:// prefix)
        check_exists: If True, skip upload if file already exists (idempotent)

    Returns:
        True if uploaded, False if skipped (exists) or failed
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)

        # Check if exists (idempotent write)
        if check_exists and blob.exists():
            msg = (
                f"File already exists at gs://{bucket_name}/{gcs_path}, "
                "skipping upload"
            )
            logger.info(msg)
            return False

        # Convert DataFrame to JSONL
        jsonl_content = ""
        for _, row in df.iterrows():
            record = row.to_dict()
            # Convert NaN to None for JSON
            record = {
                k: (None if pd.isna(v) else v)
                for k, v in record.items()
            }
            jsonl_content += json.dumps(record) + "\n"

        # Upload
        blob.upload_from_string(
            jsonl_content, content_type="application/jsonl"
        )

        msg = (
            f"Uploaded {len(df)} records to "
            f"gs://{bucket_name}/{gcs_path}"
        )
        logger.info(msg)
        return True

    except Exception as e:
        logger.error(f"Failed to upload to GCS: {e}")
        raise


def upload_raw_data(
    df: pd.DataFrame,
    vendor: str,
    ds: str,
    bucket_name: Optional[str] = None,
    check_exists: bool = True,
) -> str:
    """
    Upload raw scraped data to GCS (date-partitioned).

    Args:
        df: DataFrame with scraped data (must match fixed schema)
        vendor: Vendor identifier
        ds: Date string in YYYY-MM-DD format
        bucket_name: GCS bucket name (from env var if not provided)
        check_exists: If True, skip if file exists (idempotent)

    Returns:
        GCS path where data was uploaded
    """
    if bucket_name is None:
        bucket_name = os.getenv("GCS_RAW_BUCKET")
        if not bucket_name:
            msg = (
                "GCS bucket name must be provided or set "
                "GCS_RAW_BUCKET env var"
            )
            raise ValueError(msg)

    gcs_path = get_raw_data_path(vendor, ds)

    upload_dataframe_to_gcs(
        df, bucket_name, gcs_path, check_exists=check_exists
    )

    return f"gs://{bucket_name}/{gcs_path}"


def check_file_exists(bucket_name: str, gcs_path: str) -> bool:
    """
    Check if a file exists in GCS.

    Args:
        bucket_name: GCS bucket name
        gcs_path: GCS path (without gs:// prefix)

    Returns:
        True if file exists, False otherwise
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        blob = bucket.blob(gcs_path)
        return blob.exists()
    except Exception as e:
        logger.warning(f"Error checking file existence: {e}")
        return False


def list_partition_files(bucket_name: str, vendor: str, ds: str) -> list[str]:
    """
    List all files in a date partition.

    Args:
        bucket_name: GCS bucket name
        vendor: Vendor identifier
        ds: Date string in YYYY-MM-DD format

    Returns:
        List of GCS paths (without gs:// prefix)
    """
    try:
        client = get_gcs_client()
        bucket = client.bucket(bucket_name)
        prefix = f"raw/{vendor}/ds={ds}/"

        blobs = bucket.list_blobs(prefix=prefix)
        return [blob.name for blob in blobs]
    except Exception as e:
        logger.error(f"Error listing partition files: {e}")
        return []

import os
import logging

import psycopg2
import functions_framework
from cloudevents.http import CloudEvent

# Configure root logger; Cloud Functions will respect these levels
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@functions_framework.cloud_event
def register_document(cloud_event: CloudEvent) -> None:
    data = cloud_event.data

    # Extract GCS fields
    bucket   = data.get("bucket")
    name     = data.get("name")
    meta     = data.get("metadata", {})
    isin     = meta.get("isin")
    doc_type = meta.get("doc_type")

    # Log at INFO level
    logger.info(
        "Parsed GCS event: bucket=%r, name=%r, metadata=%r, isin=%r, doc_type=%r",
        bucket, name, meta, isin, doc_type
    )

    # Validate
    if not all([bucket, name, isin, doc_type]):
        logger.warning("Missing fields in GCS event, skipping insert.")
        return

    url = f"https://storage.googleapis.com/{bucket}/{name}"

    # Write into Postgres
    dsn = os.getenv("DB_DSN")
    if not dsn:
        logger.critical("DB_DSN environment variable is required")
        raise RuntimeError("DB_DSN environment variable is required")

    with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO documents (security_id, doc_type, url)
            SELECT id, %s, %s
              FROM securities
             WHERE isin = %s
            """,
            (doc_type, url, isin),
        )
        if cur.rowcount:
            logger.info("Registered %s for ISIN=%s", doc_type, isin)
        else:
            logger.error("No security found for ISIN=%s", isin)


@functions_framework.cloud_event
def hello_gcs(cloud_event: CloudEvent) -> tuple:
    """This function is triggered by a change in a storage bucket."""
    data = cloud_event.data

    event_id     = cloud_event["id"]
    event_type   = cloud_event["type"]
    bucket       = data.get("bucket")
    name         = data.get("name")
    metageneration = data.get("metageneration")
    timeCreated  = data.get("timeCreated")
    updated      = data.get("updated")

    # Single-line structured log
    logger.info(
        "GCS Event: id=%s type=%s bucket=%s file=%s metageneration=%s created=%s updated=%s",
        event_id, event_type, bucket, name, metageneration, timeCreated, updated
    )

    return event_id, event_type, bucket, name, metageneration, timeCreated, updated

# main.py
import os
import json
import base64
import psycopg2
import functions_framework
from cloudevents.http import CloudEvent

# Expose the Functions Framework WSGI app as "app" for Buildpacks
app = functions_framework.create_app(
    target="register_document",
    signature_type="cloudevent"
)

@functions_framework.cloud_event
async def register_document(cloud_event: CloudEvent):
    """
    Handles Pub/Sub messages wrapped in CloudEvents.
    Decodes nested GCS notification payload and inserts into Postgres.
    """
    # 1) Extract Pub/Sub message envelope
    envelope = cloud_event.data.get("message", {})
    data_b64 = envelope.get("data")
    if not data_b64:
        print("⚠️  No Pub/Sub data in CloudEvent, skipping")
        return

    # 2) Decode nested GCS notification JSON
    try:
        raw = base64.b64decode(data_b64).decode("utf-8")
        payload = json.loads(raw)
    except Exception as e:
        print(f"❌ Failed to decode nested JSON: {e}")
        return

    bucket = payload.get("bucket")
    name = payload.get("name")
    meta = payload.get("metadata", {})
    isin = meta.get("isin")
    doc_type = meta.get("doc_type")

    if not all([bucket, name, isin, doc_type]):
        print(f"⚠️  Missing fields in notification: {payload}")
        return

    url = f"https://storage.googleapis.com/{bucket}/{name}"

    # 3) Insert into Postgres
    dsn = os.environ.get("DB_DSN")
    if not dsn:
        raise RuntimeError("DB_DSN environment variable is required")

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
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
                print(f"✅ Registered {doc_type} for ISIN={isin}")
            else:
                print(f"❌ No security found for ISIN={isin}")
        conn.commit()
    finally:
        conn.close()

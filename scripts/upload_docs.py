import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account

# ── Locate and load your .env.local from the project root ───────────
ROOT_DIR = Path(__file__).parents[1]
dotenv_path = ROOT_DIR / ".env.local"
load_dotenv(dotenv_path=dotenv_path)
# ─────────────────────────────────────────────────────────────────────

# ── Build a GCS client explicitly from your service-account file ────
key_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
if not key_path or not Path(key_path).exists():
    raise RuntimeError("Service account JSON not found; "
                       "check GOOGLE_APPLICATION_CREDENTIALS in .env.local")

creds = service_account.Credentials.from_service_account_file(key_path)
client = storage.Client(credentials=creds, project=creds.project_id)
bucket = client.bucket("dry-martini-docs")
# ─────────────────────────────────────────────────────────────────────

def upload_and_mark(local_path: Path, isin: str, doc_type: str):
    """
    Uploads the file by prefixing the ISIN to the filename, bumps on collision,
    and uses explicit service-account credentials.
    """
    original_name = local_path.name
    base_stem, ext = local_path.stem, local_path.suffix  # e.g. ("report", ".pdf")

    # 1) Build the candidate stem with ISIN prefix
    candidate_stem = f"{isin}_{base_stem}"
    candidate = f"{candidate_stem}{ext}"
    counter = 1

    # 2) If the name exists, bump with _1, _2, ...
    while bucket.blob(candidate).exists():
        candidate = f"{candidate_stem}_{counter}{ext}"
        counter += 1

    # 3) Upload the blob with metadata
    blob = bucket.blob(candidate)
    blob.metadata = {
        "isin":              isin,
        "doc_type":          doc_type,
        "original_filename": original_name,
    }
    blob.upload_from_filename(str(local_path))

    print(f"Uploaded gs://{bucket.name}/{candidate} (was {original_name}) "
          f"with metadata {blob.metadata}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 4:
        print("Usage: python upload_docs.py <file_path> <isin> <doc_type>")
        sys.exit(1)

    file_path, isin, doc_type = sys.argv[1], sys.argv[2], sys.argv[3]
    local_path = Path(file_path)

    if not local_path.exists():
        print(f"Error: file not found: {file_path}")
        sys.exit(1)

    upload_and_mark(local_path, isin, doc_type)

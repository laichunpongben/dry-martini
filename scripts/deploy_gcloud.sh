gcloud functions deploy register_document   --gen2   --region=asia-southeast1   --runtime=python312   --source=./   --entry-point=register_document   --trigger-bucket=your-bucket   --set-env-vars=DB_DSN="your-postgres-dsn"

gcloud functions deploy register_document_delete \
  --gen2 \
  --region=asia-southeast1 \
  --runtime=python312 \
  --source=./ \
  --entry-point=register_document_delete \
  --trigger-event-filters="type=google.cloud.storage.object.v1.deleted" \
  --trigger-event-filters="bucket=your-bucket" \
  --set-env-vars=DB_DSN="your-postgres-dsn"
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

gcloud config set project your-project-id

gcloud auth configure-docker asia-southeast1-docker.pkg.dev
docker build -f Dockerfile -t asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-app-image:0.0.5 .
docker push asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-app-image:0.0.5
gcloud run deploy your-app-image \
  --image asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-app-image:0.0.5 \
  --region asia-southeast1 \
  --platform managed \
  --allow-unauthenticated
gcloud run services update your-app-image \
  --image asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-app-image:0.0.5 \
  --region asia-southeast1

docker build -f Dockerfile.web -t asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-web-image:0.0.2 .
docker push asia-southeast1-docker.pkg.dev/your-project-id/your-repo/your-web-image:0.0.2
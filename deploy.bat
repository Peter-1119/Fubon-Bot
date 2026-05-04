@echo off
echo ===================================================
echo   Fubon-Bot Cloud Deployment Script
echo ===================================================
echo.
echo [Step 1] Logging into Google Cloud account...
call gcloud auth login

echo.
set /p project_id="[Step 2] Please enter your GCP Project ID: "
call gcloud config set project %project_id%

echo.
echo [Step 3] Enabling required Cloud APIs (this may take 1-2 minutes)...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com storage.googleapis.com

echo.
echo [Step 4] Building and deploying to Cloud Run (asia-east1)...
echo (Note: If prompted to enable Artifact Registry, enter Y)
call gcloud run deploy fubon-bot --source . --region asia-east1 --allow-unauthenticated

echo.
echo ===================================================
echo Deployment completed successfully!
echo.
echo Next manual steps required:
echo 1. Set Environment Variables in Cloud Run (Tokens, Bucket name).
echo 2. Setup cron jobs in Cloud Scheduler.
echo 3. Update Webhook URL in LINE Developers console.
echo ===================================================
pause
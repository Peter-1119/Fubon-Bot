@echo off
chcp 65001 > nul
echo ===================================================
echo   富邦自動化機器人 (Fubon-Bot) - 雲端一鍵部署程式
echo ===================================================
echo.
echo [步驟 1] 正在登入 Google Cloud 帳號...
call gcloud auth login

echo.
set /p project_id="[步驟 2] 請輸入您的 GCP 專案 ID: "
call gcloud config set project %project_id%

echo.
echo [步驟 3] 正在啟用必要的雲端 API (這可能需要 1-2 分鐘)...
call gcloud services enable run.googleapis.com cloudbuild.googleapis.com cloudscheduler.googleapis.com storage.googleapis.com

echo.
echo [步驟 4] 準備打包程式碼並部署至 Cloud Run (台灣區)...
echo (注意：過程中若詢問建立 Artifact Registry，請輸入 Y)
call gcloud run deploy fubon-bot --source . --region asia-east1 --allow-unauthenticated

echo.
echo ===================================================
echo 🎉 程式碼部署指令執行完畢！
echo.
echo 請繼續完成以下手動設定：
echo 1. 去 Cloud Run 設定「環境變數」(Token、Bucket 名稱)。
echo 2. 去 Cloud Scheduler 設定「定時鬧鐘」。
echo 3. 將網址貼回 LINE 後台。
echo ===================================================
pause
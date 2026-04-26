@echo off
echo ===================================================
echo   富邦自動化機器人 (Fubon-Bot) - 雲端一鍵部署程式
echo ===================================================
echo.
echo [步驟 1] 正在登入 Google Cloud...
call gcloud auth login

echo.
set /p project_id="[步驟 2] 請輸入您的 GCP 專案 ID: "
call gcloud config set project %project_id%

echo.
echo [步驟 3] 準備打包並部署至 Cloud Run (亞洲台灣區)...
call gcloud run deploy fubon-bot --source . --region asia-east1 --allow-unauthenticated

echo.
echo ===================================================
echo 部署指令執行完畢！
echo 請至 GCP 控制台設定環境變數，並將網址貼至 LINE 後台。
echo ===================================================
pause
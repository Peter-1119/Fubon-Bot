# Fubon-Bot: Automated LINE Office Assistant 🤖📈

A Python-based LINE Bot designed for Fubon Life Insurance teams to automate daily reporting, performance tracking, and attendance monitoring. Built with Flask and deployed on Google Cloud Platform (GCP) utilizing a Serverless architecture.

## ✨ Features

* **Automated Performance Tracking:** * ⚠️ Sends warnings to managers for agents underperforming.
  * 🎉 Sends congratulatory messages (Fubon Star) to the staff group when milestones are reached.
* **Attendance Monitoring:** Automatically checks and reports staff members who missed clock-ins on weekdays at 5:00 PM.
* **Financial Leaderboards:** Generates monthly/yearly salary and bonus ranking reports.
* **Hybrid Storage Architecture:** * `development` mode: Reads/writes to local `.json` files for rapid testing.
  * `production` mode: Seamlessly integrates with Google Cloud Storage for persistent, stateless execution.
* **Dynamic Admin Control:** Administrators can update system credentials and manually trigger report dispatches directly via LINE chat, without needing to redeploy the code.
* **Automated Captcha Solving:** Integrates OpenCV to bypass login verification systems seamlessly.

## 🛠️ Technology Stack

* **Language:** Python 3.10
* **Framework:** Flask, Gunicorn
* **Deployment:** Docker, Google Cloud Run
* **Storage:** Google Cloud Storage
* **Automation:** Google Cloud Scheduler
* **Integration:** LINE Messaging API

## 📋 Prerequisites

Before you begin, ensure you have met the following requirements:
* A [LINE Developers](https://developers.line.biz/en/) account and a Messaging API channel.
* A [Google Cloud Platform (GCP)](https://console.cloud.google.com/) account.
* Docker installed on your local machine (for local testing).

## 💻 Local Development

1. **Clone the repository:**
```bash
git clone [https://github.com/Your-Username/Fubon-Bot.git](https://github.com/Your-Username/Fubon-Bot.git)
cd Fubon-Bot
```

2. **Create a `.env` file in the root directory:**
APP_ENV=development
LINE_CHANNEL_TOKEN=your_line_channel_access_token_here
SETUP_PASSWORD=your_secret_admin_password

3. **Build and run with Docker:**
docker build -t fubon-bot-local .
docker run -p 8080:8080 --env-file .env -e PORT=8080 fubon-bot-local

4. **Test the cron jobs manually via browser:**
Navigate to `http://localhost:8080/run/all_tasks?hour=12&weekday=2`

## ☁️ GCP Deployment (Production)
1. **Enable GCP APIs: Ensure Cloud Run, Cloud Build, Cloud Storage, and Cloud Scheduler APIs are enabled in your GCP project.**

2. **Create a Cloud Storage Bucket: Create a bucket (e.g., in `us-central1` for Free Tier eligibility) to store settings and history.**

3. **Deploy using Google Cloud CLI:**
```bash
gcloud run deploy fubon-bot --source . --region asia-east1 --allow-unauthenticated
```

4. **Configure Environment Variables in Cloud Run:**
* `APP_ENV` = `production`
* `GCS_BUCKET_NAME` = `<your-bucket-name>`
* `LINE_CHANNEL_TOKEN` = `<your-line-token>`
* `SETUP_PASSWORD` = `<your-password>`

5. **Update LINE Webhook: Set your LINE Webhook URL to `https://<your-cloud-run-url>/callback` and disable "Webhook Redelivery".**

## 📱 Bot Commands
| **Command** | **Environment** | **Description** |
| --- | --- | --- |
| `[SETUP_PASSWORD]` | 1-on-1 Chat| Binds the user as the system Administrator. |
| `更新帳密 [account] [password]` | 1-on-1 Chat | Updates the Fubon system login credentials (Admin only). |
| `補發業績 / 補發賀報 / 補發薪資` | 1-on-1 Chat | Manually triggers specific reports to the designated groups. |
| `設定大群組` | Group Chat | Binds the current group as the "All Staff" broadcast group (Admin only). |
| `設定主管群` | Group Chat | Binds the current group as the "Manager Only" warning group (Admin only). |

## ⚠️ Disclaimer
This project is an independent automation tool built for administrative efficiency. It is not officially affiliated with, endorsed by, or connected to Fubon Life Insurance Co., Ltd. Users are responsible for ensuring compliance with their organization's data security and privacy policies when deploying this bot.
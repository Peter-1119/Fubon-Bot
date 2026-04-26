import os
import json

# 判斷當前環境，預設為 development
APP_ENV = os.getenv("APP_ENV", "development")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "fubon-bot-storage-us")

# --- GCS 雲端存取邏輯 ---
def _gcs_read(filename, default_data):
    from google.cloud import storage
    try:
        client = storage.Client()
        blob = client.bucket(BUCKET_NAME).blob(filename)
        if blob.exists():
            return json.loads(blob.download_as_text())
    except Exception as e:
        print(f"[GCS] 讀取 {filename} 失敗: {e}")
    return default_data

def _gcs_write(filename, data):
    from google.cloud import storage
    try:
        client = storage.Client()
        blob = client.bucket(BUCKET_NAME).blob(filename)
        blob.upload_from_string(json.dumps(data, ensure_ascii=False, indent=4))
    except Exception as e:
        print(f"[GCS] 寫入 {filename} 失敗: {e}")

# --- 本地存取邏輯 ---
def _local_read(filename, default_data):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return default_data

def _local_write(filename, data):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ==========================================
# 對外公開的統一介面 (Facade Pattern)
# ==========================================
def read_json(filename, default_data):
    if APP_ENV == "production":
        return _gcs_read(filename, default_data)
    else:
        return _local_read(filename, default_data)

def write_json(filename, data):
    if APP_ENV == "production":
        _gcs_write(filename, data)
    else:
        _local_write(filename, data)
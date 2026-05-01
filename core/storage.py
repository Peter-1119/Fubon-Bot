import os, io, json, tempfile

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

def upload_image_to_gcs(image_object, filename):
    """
    將 Pillow 的 Image 物件直接上傳到 GCS，不落地(不存入本地硬碟)。
    回傳該圖片的公開 HTTPS 網址。
    """
    if APP_ENV != "production":
        # 本地測試時，還是可以存一份在本地端方便查看
        temp_path = os.path.join(tempfile.gettempdir(), filename)
        image_object.save(temp_path, format="JPEG", quality=90)
        return f"http://127.0.0.1:8080/images/{filename}" # 測試用的假網址

    from google.cloud import storage
    try:
        client = storage.Client()
        bucket = client.bucket(BUCKET_NAME)
        blob = bucket.blob(f"images/{filename}") # 存在 images/ 資料夾下
        
        # 將圖片轉換為二進位流 (Byte Stream)
        byte_stream = io.BytesIO()
        image_object.save(byte_stream, format="JPEG", quality=90)
        byte_stream.seek(0)
        
        # 上傳到 GCS
        blob.upload_from_file(byte_stream, content_type="image/jpeg")
        
        # 回傳 GCS 的絕對網址給 LINE 讀取
        return f"https://storage.googleapis.com/{BUCKET_NAME}/images/{filename}"
    except Exception as e:
        print(f"[GCS] 上傳圖片 {filename} 失敗: {e}")
        return None
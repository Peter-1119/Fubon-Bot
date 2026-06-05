import uuid, os, glob, tempfile
from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.storage import upload_image_to_gcs

# --- 配置參數 (可根據底圖位置微調) ---
PHOTO_CENTER_X = 964 // 2   # 圓心在 template2.jpg 的 X 座標
PHOTO_CENTER_Y = 560   # 圓心在 template2.jpg 的 Y 座標
PHOTO_RADIUS = 297     # 圓形的半徑
ANTIALIAS_SCALE = 4    # 抗鋸齒縮放倍率 (越高越平滑，但也越慢)

def find_and_download_user_photo_from_gcs(name):
    """從 GCS Bucket 的 photos/ 目錄中尋找該人名圖片並下載到暫存區"""
    from google.cloud import storage
    try:
        bucket_name = os.getenv("GCS_BUCKET_NAME", "fubon-bot-storage-us")
        client = storage.Client()
        bucket = client.bucket(bucket_name)
        
        # 列出 photos/ 目錄下的檔案
        blobs = client.list_blobs(bucket, prefix="photos/")
        for blob in blobs:
            filename = os.path.basename(blob.name)
            # 判斷檔名(排除路徑)中是否包含人名
            if name in filename and filename != "":
                _, ext = os.path.splitext(filename)
                temp_dir = tempfile.gettempdir()
                # 建立唯一的暫存路徑
                temp_file_path = os.path.join(temp_dir, f"gcs_photo_{name}{ext}")
                blob.download_to_filename(temp_file_path)
                print(f"☁️ [GCS] 成功下載 {name} 的照片至: {temp_file_path}")
                return temp_file_path
    except Exception as e:
        print(f"⚠️ [GCS] 尋找或下載 {name} 的照片失敗: {e}")
    return None

def find_user_photo(name):
    """尋找同仁照片。若為生產環境則從 GCS 下載，否則使用本地 templates/photos"""
    if os.getenv("APP_ENV", "development") == "production":
        return find_and_download_user_photo_from_gcs(name)
        
    # 本地測試環境：使用 templates/photos
    search_pattern = f"templates/photos/*{name}*"
    files = glob.glob(search_pattern)
    if files:
        return files[0]
    return None

def process_circle_mask(photo_path, radius):
    """處理圓形遮罩：裁切、抗鋸齒圓形"""
    try:
        with Image.open(photo_path) as img:
            # 1. 轉為 RGBA 確保有 Alpha 通道
            img = img.convert("RGBA")
            
            # 2. 正方形裁切 (由上方開始)
            size = (radius * 2, radius * 2)
            img = ImageOps.fit(img, size, centering=(0.5, 0.15))
            
            # 3. 建立高品質圓形遮罩 (放大繪製再縮小以達成抗鋸齒)
            mask_size = (size[0] * ANTIALIAS_SCALE, size[1] * ANTIALIAS_SCALE)
            mask = Image.new('L', mask_size, 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, mask_size[0], mask_size[1]), fill=255)
            mask = mask.resize(size, resample=Image.LANCZOS)
            
            # 4. 套用遮罩
            output = Image.new('RGBA', size, (0, 0, 0, 0))
            output.paste(img, (0, 0), mask=mask)
            return output
    except Exception as e:
        print(f"❌ 處理圓形遮罩失敗: {e}")
        return None

def generate_local_congrats(name, diff_amount, total_amount=None):
    """產生賀報圖片"""
    font_path = "fontStyles/LXGWWenKaiTC-Bold.ttf"
    photo_path = find_user_photo(name)
    
    # 決定使用哪張底圖
    if photo_path:
        template_path = "templates/template2.jpg"
        use_photo = True
    else:
        template_path = "templates/template1.jpg"
        use_photo = False
        
    if not os.path.exists(template_path):
        print(f"❌ 找不到底圖：{template_path}")
        return None
        
    try:
        img = Image.open(template_path).convert("RGB")
        draw = ImageDraw.Draw(img)
        img_w, img_h = img.size

        # --- 1. 合成個人照 (僅限 template2) ---
        if use_photo:
            person_img = process_circle_mask(photo_path, PHOTO_RADIUS)
            if person_img:
                # 計算貼上位置 (左上角座標)
                paste_x = PHOTO_CENTER_X - PHOTO_RADIUS
                paste_y = PHOTO_CENTER_Y - PHOTO_RADIUS
                img.paste(person_img, (paste_x, paste_y), mask=person_img)

        # --- 2. 繪製文字 (位置與字體大小根據底圖調整) ---
        if use_photo:
            # Template 2 的文字佈局
            name_font = ImageFont.truetype(font_path, 150)
            diff_font = ImageFont.truetype(font_path, 120)
            
            # 姓名
            name_bbox = draw.textbbox((0, 0), name, font=name_font)
            name_w = name_bbox[2] - name_bbox[0]
            draw.text(((img_w - name_w) / 2, img_h * 0.57), name, font=name_font, fill=(255, 228, 149))
            
            # 差額
            diff_text = f"{diff_amount:,}"
            diff_bbox = draw.textbbox((0, 0), diff_text, font=diff_font)
            diff_w = diff_bbox[2] - diff_bbox[0]
            draw.text(((img_w * 0.5) - (diff_w / 2), img_h * 0.68), diff_text, font=diff_font, fill=(255, 228, 149))
        else:
            # Template 1 的文字佈局
            name_font = ImageFont.truetype(font_path, 250)
            diff_font = ImageFont.truetype(font_path, 120)

            name_bbox = draw.textbbox((0, 0), name, font=name_font)
            name_w = name_bbox[2] - name_bbox[0]
            draw.text(((img_w - name_w) / 2, img_h * 0.4), name, font=name_font, fill=(227, 185, 115))

            diff_text = f"{diff_amount:,}"
            diff_bbox = draw.textbbox((0, 0), diff_text, font=diff_font)
            diff_w = diff_bbox[2] - diff_bbox[0]
            draw.text(((img_w * 0.40) - (diff_w / 2), img_h * 0.71), diff_text, font=diff_font, fill=(30, 30, 30))

        # 產生唯一檔名並上傳
        filename = f"congrats_{uuid.uuid4().hex[:6]}.jpg"
        image_url = upload_image_to_gcs(img, filename)
        
        print(f"✅ 圖片已產生並取得網址：{image_url} (使用照片: {use_photo})")
        return image_url

    except Exception as e:
        print(f"❌ 製圖失敗: {e}")
        return None

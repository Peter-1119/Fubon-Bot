import os
import time
import uuid
import tempfile # 新增這個！
from PIL import Image, ImageDraw, ImageFont

# 自動取得系統的暫存資料夾 (Windows 會是 C:\Users\...\AppData\Local\Temp，Cloud Run 會是 /tmp)
TEMP_DIR = tempfile.gettempdir()

def cleanup_expired_images(max_age_seconds=600):
    """【自動清道夫】清理超過 10 分鐘 (600秒) 的舊賀報"""
    now = time.time()
    
    for filename in os.listdir(TEMP_DIR):
        if filename.startswith("congrats_") and filename.endswith(".jpg"):
            filepath = os.path.join(TEMP_DIR, filename)
            try:
                file_mtime = os.path.getmtime(filepath)
                if now - file_mtime > max_age_seconds:
                    os.remove(filepath)
                    print(f"🧹 已清理過期圖片: {filename}")
            except Exception as e:
                pass

def generate_local_congrats(name, fyc_amount):
    """產生圖片並存入暫存區，回傳檔名"""
    cleanup_expired_images()

    template_path = "templates/template1.jpg"
    font_path = "fontStyles/LXGWWenKaiTC-Bold.ttf"
    
    if not os.path.exists(template_path):
        print(f"❌ 找不到底圖：{template_path}")
        return None
        
    try:
        img = Image.open(template_path)
        draw = ImageDraw.Draw(img)
        img_w, img_h = img.size

        name_font = ImageFont.truetype(font_path, 250)
        fyc_font = ImageFont.truetype(font_path, 120)

        # 繪製邏輯保持不變...
        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_w = name_bbox[2] - name_bbox[0]
        draw.text(((img_w - name_w) / 2, img_h * 0.4), name, font=name_font, fill=(227, 185, 115))

        fyc_text = f"{fyc_amount:,}"
        fyc_bbox = draw.textbbox((0, 0), fyc_text, font=fyc_font)
        fyc_w = fyc_bbox[2] - fyc_bbox[0]
        draw.text(((img_w * 0.40) - (fyc_w / 2), img_h * 0.71), fyc_text, font=fyc_font, fill=(30, 30, 30))

        # 產生唯一檔名，並存入系統暫存區
        filename = f"congrats_{uuid.uuid4().hex[:6]}.jpg"
        temp_path = os.path.join(TEMP_DIR, filename) # 使用跨平台路徑組合
        img.save(temp_path, format="JPEG", quality=90)
        
        print(f"✅ 圖片已產生於暫存區：{temp_path}")
        return filename

    except Exception as e:
        print(f"❌ 製圖失敗: {e}")
        return None
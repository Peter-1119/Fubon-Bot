import uuid, os
from PIL import Image, ImageDraw, ImageFont
from core.storage import upload_image_to_gcs

def generate_local_congrats(name, fyc_amount):
    """產生圖片並直接丟上 GCS，回傳絕對網址"""
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

        name_bbox = draw.textbbox((0, 0), name, font=name_font)
        name_w = name_bbox[2] - name_bbox[0]
        draw.text(((img_w - name_w) / 2, img_h * 0.4), name, font=name_font, fill=(227, 185, 115))

        fyc_text = f"{fyc_amount:,}"
        fyc_bbox = draw.textbbox((0, 0), fyc_text, font=fyc_font)
        fyc_w = fyc_bbox[2] - fyc_bbox[0]
        draw.text(((img_w * 0.40) - (fyc_w / 2), img_h * 0.71), fyc_text, font=fyc_font, fill=(30, 30, 30))

        # 產生唯一檔名，直接呼叫上傳功能
        filename = f"congrats_{uuid.uuid4().hex[:6]}.jpg"
        image_url = upload_image_to_gcs(img, filename)
        
        print(f"✅ 圖片已產生並取得網址：{image_url}")
        return image_url # 這裡回傳的直接是 https://... 的網址了！

    except Exception as e:
        print(f"❌ 製圖失敗: {e}")
        return None
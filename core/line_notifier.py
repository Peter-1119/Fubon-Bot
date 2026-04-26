import requests
import config

def send_line_message(group_id, text_message):
    """【主動推播】定時發報表用"""
    if not text_message or not group_id: return
        
    url = "https://api.line.me/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_TOKEN}"
    }
    payload = {"to": group_id, "messages": [{"type": "text", "text": text_message}]}
    requests.post(url, headers=headers, json=payload)

def reply_line_message(reply_token, text_message):
    """【被動回覆】客戶輸入指令時，馬上回傳確認訊息"""
    if not text_message or not reply_token: return

    url = "https://api.line.me/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {config.LINE_TOKEN}"
    }
    payload = {"replyToken": reply_token, "messages": [{"type": "text", "text": text_message}]}
    requests.post(url, headers=headers, json=payload)
import os
from datetime import datetime
from flask import Flask, jsonify, request

from config import SETUP_PASSWORD
from core.bot_client import FubonAutoBot
from core.storage import read_json, write_json
from core import line_notifier
import tasks.report_tasks as tasks

app = Flask(__name__)
bot_instance = None

# --- 群組 ID 存取工具 (本地測試版) ---
SETTINGS_FILE = 'group_settings.json'
DEFAULT_SETTINGS = {"admin_user_id": "", "manager_group": "", "all_staff_group": "", "fubon_account": "", "fubon_password": ""}

def get_group_settings():
    return read_json(SETTINGS_FILE, DEFAULT_SETTINGS)

def save_group_settings(settings_data):
    write_json(SETTINGS_FILE, settings_data)
    
def get_bot():
    """動態讀取帳密，登入失敗直接推播給管理員，並銷毀失效的 Cookie"""
    global bot_instance
    
    settings = get_group_settings()
    account = settings.get("fubon_account", "")
    password = settings.get("fubon_password", "")
    admin_id = settings.get("admin_user_id", "")

    if not account or not password:
        if admin_id:
            line_notifier.send_line_message(admin_id, "⚠️ 系統尚未設定富邦帳號密碼！\n請在此輸入「更新帳密 [您的帳號] [您的密碼]」來完成設定。")
        print("[錯誤] 尚未設定帳號密碼")
        return None

    if bot_instance is None or not bot_instance.is_logged_in():
        bot_instance = FubonAutoBot()
        bot_instance.load_cookies()
        
        if not bot_instance.is_logged_in():
            print(f"🚀 執行全自動登入程序... (帳號: {account})")
            success = bot_instance.execute_login(account, password)
            
            if success:
                bot_instance.save_cookies()
            else:
                # 【防護攔截】登入失敗，發送警告給管理員，並刪除壞掉的本地快取！
                if admin_id:
                    line_notifier.send_line_message(admin_id, "❌ 目前資訊返回失敗，請確認帳號密碼或系統是否正常。")
                
                if os.path.exists("fubon_cookies.pkl"):
                    os.remove("fubon_cookies.pkl")
                    
                bot_instance = None 
                return None
                
    return bot_instance

@app.route('/callback', methods=['POST'])
def callback():
    """接收客戶指令，包含綁定與手動補發"""
    json_data = request.get_json()
    
    try:
        events = json_data.get("events", [])
        for event in events:
            if event.get("type") == "message" and event["message"].get("type") == "text":
                text = event["message"]["text"].strip()
                reply_token = event.get("replyToken")
                
                source = event.get("source", {})
                source_type = source.get("type")
                user_id = source.get("userId")
                group_id = source.get("groupId")
                
                settings = get_group_settings()
                admin_id = settings.get("admin_user_id")
                
                # 狀況 A：客戶在【1對1私訊】
                if source_type == "user":
                    if text == SETUP_PASSWORD:
                        settings["admin_user_id"] = user_id
                        save_group_settings(settings)
                        line_notifier.reply_line_message(reply_token, "👑 系統提示：管理員身分綁定成功！\n請接著輸入「更新帳密 [帳號] [密碼]」。")
                    
                    elif text.startswith("更新帳密"):
                        if user_id != admin_id:
                            line_notifier.reply_line_message(reply_token, "⛔ 權限不足，請先輸入通關密語綁定身分。")
                            continue
                            
                        parts = text.split(" ")
                        if len(parts) == 3:
                            settings["fubon_account"] = parts[1]
                            settings["fubon_password"] = parts[2]
                            save_group_settings(settings)
                            line_notifier.reply_line_message(reply_token, f"✅ 帳密更新成功！綁定帳號為：{parts[1]}")
                        else:
                            line_notifier.reply_line_message(reply_token, "⚠️ 格式錯誤！請輸入：更新帳密 [帳號] [密碼]")

                    # ==========================================
                    # 【新增功能】手動補發監聽 (單線程同步執行)
                    # ==========================================
                    elif text in ["補發業績", "補發賀報", "補發薪資", "補發年終"]:
                        if user_id != admin_id:
                            line_notifier.reply_line_message(reply_token, "⛔ 權限不足，只有管理員可以執行補發。")
                            continue
                        
                        # 先用 Reply API 快速安撫使用者
                        line_notifier.reply_line_message(reply_token, f"⏳ 收到指令：【{text}】\n系統正在為您抓取最新資料，請稍候...")

                        # 同步開始爬蟲 (會卡住伺服器，直到跑完才回傳 200 OK)
                        bot = get_bot()
                        if not bot: continue # 密碼錯誤已在 get_bot 內通報，直接結束

                        manager_group = settings.get("manager_group")
                        staff_group = settings.get("all_staff_group")

                        if text == "補發業績":
                            res = tasks.task_check_performance(bot, mode="warning")
                            if res["warnings"] and manager_group:
                                msg = "⚠️【主管業績警示(手動補發)】\n" + "\n".join(res["warnings"])
                                line_notifier.send_line_message(manager_group, msg)
                            line_notifier.send_line_message(admin_id, "✅ 業績警示處理完畢。(已發送過的主管不會重複洗版)")

                        elif text == "補發賀報":
                            res = tasks.task_check_performance(bot, mode="congrats")
                            if (res.get("congrats") or res.get("big_congrats")) and staff_group:
                                congrats_list = res.get("big_congrats", []) + res.get("congrats", [])
                                msg = "🏆【富邦之星賀報(手動補發)】\n" + "\n".join(congrats_list)
                                line_notifier.send_line_message(staff_group, msg)
                            line_notifier.send_line_message(admin_id, "✅ 賀報處理完畢。(已發送過的人員不會重複洗版)")

                        elif text == "補發薪資":
                            res = tasks.task_salary_top10(bot)
                            if res and staff_group:
                                msg = "💰【本年度所得累計 Top 10 (手動補發)】\n"
                                for i, val in enumerate(res):
                                    msg += f"第 {i+1} 名: {val:,} 元\n"
                                line_notifier.send_line_message(staff_group, msg)
                            line_notifier.send_line_message(admin_id, "✅ 薪資排行發送完畢。")

                        elif text == "補發年終":
                            res = tasks.task_yearly_bonus(bot)
                            if res and staff_group:
                                msg = "📊【本月年度核實業績(手動補發)】\n" + "\n".join(res)
                                line_notifier.send_line_message(staff_group, msg)
                            line_notifier.send_line_message(admin_id, "✅ 年終核實報表發送完畢。")

                    elif text in ["設定大群組", "設定主管群"]:
                        line_notifier.reply_line_message(reply_token, "⚠️ 請把我邀請進群組後，在『群組內』輸入此指令喔！")
                        
                # 狀況 B：客戶在【群組】內進行綁定
                elif source_type == "group":
                    if text in ["設定大群組", "設定主管群"]:
                        if user_id != admin_id:
                            continue

                        if text == "設定大群組":
                            settings["all_staff_group"] = group_id
                            save_group_settings(settings)
                            line_notifier.reply_line_message(reply_token, "✅ 綁定成功：此群組已設為【富邦大群組】！")
                        elif text == "設定主管群":
                            settings["manager_group"] = group_id
                            save_group_settings(settings)
                            line_notifier.reply_line_message(reply_token, "✅ 綁定成功：此群組已設為【主管群】！")
                            
    except Exception as e:
        print(f"Webhook 處理失敗: {e}")
        
    return 'OK', 200

@app.route('/run/performance', methods=['GET'])
def api_performance():
    res = tasks.task_check_performance(get_bot())
    return jsonify({"status": "success", "data": res})

@app.route('/run/attendance', methods=['GET'])
def api_attendance():
    res = tasks.task_attendance(get_bot())
    return jsonify({"status": "success", "absent_staff": res})

@app.route('/run/salary', methods=['GET'])
def api_salary():
    res = tasks.task_salary_top10(get_bot())
    return jsonify({"status": "success", "top10_salaries": res})

@app.route('/run/yearly', methods=['GET'])
def api_yearly():
    res = tasks.task_yearly_bonus(get_bot())
    return jsonify({"status": "success", "yearly_bonus": res})

@app.route('/run/all_tasks', methods=['GET'])
def run_master_cron():
    now = datetime.now()
    
    test_hour = request.args.get('hour')
    test_weekday = request.args.get('weekday')
    test_day = request.args.get('day')
    
    hour = int(test_hour) if test_hour is not None else now.hour
    weekday = int(test_weekday) if test_weekday is not None else now.weekday()
    day = int(test_day) if test_day is not None else now.day
    
    bot = get_bot()
    if not bot:
        return jsonify({"status": "failed", "message": "Bot登入失敗或尚未設定帳密，已通知管理員。"})

    report_log = []
    settings = get_group_settings()
    manager_group = settings.get("manager_group")
    staff_group = settings.get("all_staff_group")

    if hour == 12:
        if weekday in [0, 4]:
            res = tasks.task_check_performance(bot, mode="warning")
            if res["warnings"] and manager_group:
                msg = "⚠️【主管業績警示】\n" + "\n".join(res["warnings"])
                line_notifier.send_line_message(manager_group, msg)
            report_log.append("執行週一/五主管業績警示")

        if weekday == 2:
            res = tasks.task_check_performance(bot, mode="congrats")
            if (res.get("congrats") or res.get("big_congrats")) and staff_group:
                congrats_list = res.get("big_congrats", []) + res.get("congrats", [])
                msg = "🏆【本週富邦之星賀報】\n" + "\n".join(congrats_list)
                line_notifier.send_line_message(staff_group, msg)
            report_log.append("執行週三職員賀報")

        if day == 15:
            res = tasks.task_yearly_bonus(bot)
            if res and staff_group:
                msg = "📊【本月年度核實業績】\n" + "\n".join(res)
                line_notifier.send_line_message(staff_group, msg)
            report_log.append("執行 15 號年終核實")

        if day == 25:
            res = tasks.task_salary_top10(bot)
            if res and staff_group:
                msg = "💰【本年度所得累計 Top 10】\n"
                for i, val in enumerate(res):
                    msg += f"第 {i+1} 名: {val:,} 元\n"
                line_notifier.send_line_message(staff_group, msg)
            report_log.append("執行 25 號薪資排行")

    if hour == 17:
        if weekday <= 4:
            res = tasks.task_attendance(bot)
            if res and staff_group:
                msg = "📅【今日出缺席未打卡名單】\n" + "\n".join(res)
                line_notifier.send_line_message(staff_group, msg)
            report_log.append("執行平日出缺席檢查")

    return jsonify({"status": "cron_finished", "test_time": {"hour": hour, "weekday": weekday, "day": day}, "logs": report_log})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
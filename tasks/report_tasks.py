from datetime import datetime
import payloads
import config

from core.parsers import extract_table_data, parse_agent_list
from core.storage import read_json, write_json

# --- 記憶體存取小工具 ---
# 改版後的結構： {"last_fyc_map": {"姓名": 12345}, "last_check_date": "20260603"}
HISTORY_FILE = "congrats_history.json"
DEFAULT_HISTORY = {"last_fyc_map": {}, "last_check_date": ""}

def get_memory():
    return read_json(HISTORY_FILE, DEFAULT_HISTORY)

def save_memory(data):
    write_json(HISTORY_FILE, data)
# ------------------------

def task_check_performance(bot, mode="all"):
    """
    績效檢查核心邏輯
    mode="daily_congrats": 偵測與昨日的差額，產生賀報
    mode="weekly_status": 週一、五顯示達標/未達標狀態
    mode="all": 兩者皆執行 (預留)
    """
    html_string = bot.fetch_api_html("/SAVLife/Item0028/Query", payloads.get_performance_params(bot))
    table_data = extract_table_data(html_string, target_class='report-table')
    
    memory = get_memory()
    now = datetime.now()
    today_str = now.strftime("%Y%m%d")
    is_26th = (now.day == 26)
    
    res = {
        "manager_passed": [], 
        "manager_warnings": [], 
        "staff_passed": [],
        "staff_warnings": [],
        "congrats_raw": []  # 用於發送賀報圖片的人員名單
    }

    last_fyc_map = memory.get("last_fyc_map", {})
    new_fyc_map = {} # 用於更新記憶體

    for row in table_data:
        if len(row) < 11: continue
        
        name = row[2].replace("明細", "").strip()
        supervisor = row[3].strip()
        try:
            today_cumulative_fyc = int(row[10].replace(',', ''))
            today_fyc = int(row[6].replace(',', ''))
        except:
            continue
        
        new_fyc_map[name] = today_cumulative_fyc
        
        # --- 邏輯 A: 每日賀報 (差額偵測) ---
        if mode in ["all", "daily_congrats"]:
            last_cumulative = last_fyc_map.get(name)
            
            diff = 0
            if is_26th and memory.get("last_check_date") != today_str:
                # 26 號當天第一次執行：直接看累計是否大於 0
                if today_cumulative_fyc > 0:
                    diff = today_cumulative_fyc
            elif last_cumulative is None:
                # 第一次執行且非 26 號：差額取「當日 FYC」(col[6])
                diff = today_fyc
            else:
                # 一般日：與上次紀錄的「累計 FYC」比較
                diff = today_cumulative_fyc - last_cumulative
                
            if diff > 0:
                res["congrats_raw"].append({
                    "name": name, 
                    "diff": diff, 
                    "total": today_cumulative_fyc
                })

        # --- 邏輯 B: 每週狀態 (達標 30000 門檻) ---
        if mode in ["all", "weekly_status"]:
            status_line = f"• {name} 累積：{today_cumulative_fyc:,}"
            if name == supervisor:
                if today_cumulative_fyc >= 30000:
                    res["manager_passed"].append(f"✅ {name} 累積：{today_cumulative_fyc:,}")
                else:
                    res["manager_warnings"].append(f"⚠️ {name} 累積：{today_cumulative_fyc:,} (未達3萬)")
            else:
                if today_cumulative_fyc >= 30000:
                    res["staff_passed"].append(f"✅ {name} 累積：{today_cumulative_fyc:,}")
                else:
                    res["staff_warnings"].append(f"⚠️ {name} 累積：{today_cumulative_fyc:,} (未達3萬)")

    # 更新記憶體 (不論 mode 為何，都保持最新的業績數字)
    memory["last_fyc_map"] = new_fyc_map
    memory["last_check_date"] = today_str
    save_memory(memory)

    return res

def task_attendance(bot):
    """Task 4: 出缺席檢查 (排除六日)"""
    # 取得星期幾 (0=週一, 5=週六, 6=週日)
    weekday = datetime.now().weekday()
    if weekday >= 5:
        print("[系統] 今日為週末，跳過出缺席統計。")
        return []

    html_string = bot.fetch_api_html("/SAVLife/Item0535/Query", payloads.get_attendance_params())
    table_data = extract_table_data(html_string, target_class='report-table')
    
    absent_list = []
    for row in table_data:
        # 確保陣列長度足夠，出席時間在 index 10
        if len(row) > 10:
            name = row[5].strip()
            attend_time = row[10].strip()
            
            if not attend_time or attend_time > "08:55":
                absent_list.append(name)
            
    return absent_list

def task_salary(bot):
    """Task 5: 薪資前十名 (使用「年終報表」作為正職白名單進行過濾)"""
    print("[系統] 開始執行 Task 5: 薪資排行榜...")

    # ==========================================
    # 步驟一：取得「年終資料」建立正職白名單 (Source of Truth)
    # ==========================================
    html_string_yearly = bot.fetch_api_html("/SAVLife/Item0272/FYCBonusInfo", payloads.get_yearly_bonus_params())
    table_data_yearly = extract_table_data(html_string_yearly, target_class='report-table')
    
    valid_staff_names = set() 
    for row in table_data_yearly:
        if len(row) > 11:
            name = row[4].strip() 
            valid_staff_names.add(name)
            
    print(f"[系統] 成功建立正職白名單，共 {len(valid_staff_names)} 人。")
    if not valid_staff_names:
        return [] 

    # ==========================================
    # 步驟二：取得「薪資系統」的所有人員名單
    # ==========================================
    raw_str = bot.fetch_api_raw_string("/SAVLife/Salary0001/InitUnitList", payloads.get_personal_list_params())
    roster = parse_agent_list(raw_str)
    
    salaries = []
    
    # ==========================================
    # 🌟 核心修正：動態推算「最近一次發薪日 (25號)」
    # ==========================================
    now = datetime.now()
    target_year = now.year
    target_month = now.month
    
    # 如果今天還沒過 25 號，就往前推一個月
    if now.day < 25:
        target_month -= 1
        # 如果當前是 1 月，往前推會變成 0，要修正為去年的 12 月
        if target_month == 0:
            target_month = 12
            target_year -= 1

    roc_year = target_year - 1911
    query_date = f"{roc_year}/{target_month:02d}/25"
    print(f"[系統] 薪資查詢目標日期自動校正為: {query_date}")
    
    # ==========================================
    # 步驟三：交叉比對與抓取薪資
    # ==========================================
    for agent_id, agent_name in roster.items():
        if agent_name.strip() not in valid_staff_names:
            print(f"  -> 略過非正職/無考核人員: {agent_name}")
            continue
            
        params = payloads.get_salary_params(agent_id, query_date)
        html_string = bot.fetch_api_html("/SAVLife/Salary0001/Query", params)
        
        table_data = extract_table_data(html_string, target_class='report-table', table_index=4)
        
        if table_data and len(table_data) > 0 and len(table_data[0]) > 1:
            salary_str = table_data[0][1].replace(',', '')
            if salary_str.isdigit():
                salaries.append(int(salary_str))

    # ==========================================
    # 步驟四：排序並回傳全部
    # ==========================================
    salaries.sort(reverse=True)
    return salaries

def task_yearly_bonus(bot):
    """Task 6: 年終核實"""
    html_string = bot.fetch_api_html("/SAVLife/Item0272/FYCBonusInfo", payloads.get_yearly_bonus_params())
    table_data = extract_table_data(html_string, target_class='report-table')
    
    results = []
    for row in table_data:
        if len(row) > 22:
            name = row[4]
            bonus = row[22]
            results.append(f"{name}: {bonus}")
    return results

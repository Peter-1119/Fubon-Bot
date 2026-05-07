from datetime import datetime
import payloads
import config

from core.parsers import extract_table_data, parse_agent_list
from core.storage import read_json, write_json

# --- 記憶體存取小工具 ---
HISTORY_FILE = "congrats_history.json"
DEFAULT_HISTORY = {"month": "", "sent_names": []}

def get_memory():
    return read_json(HISTORY_FILE, DEFAULT_HISTORY)

def save_memory(data):
    write_json(HISTORY_FILE, data)
# ------------------------

def task_check_performance(bot, mode="all"):
    """Task 1, 2, 3: 績效邏輯優化與記憶過濾"""
    html_string = bot.fetch_api_html("/SAVLife/Item0028/Query", payloads.get_performance_params(bot))
    table_data = extract_table_data(html_string, target_class='report-table')
    
    memory = get_memory()
    current_month = config.get_dynamic_dates()["TODAY_YYYYMMDD"][:6] 
    if memory.get("month") != current_month:
        memory = {"month": current_month, "sent_names": []} # 換月自動清空紀錄
        
    res = {
        "manager_passed": [], 
        "manager_warnings": [], 
        "congrats": [], 
        "congrats_raw": [], 
        "big_congrats_raw": []
    }

    for row in table_data:
        if len(row) < 11: continue
        
        name = row[2].replace("明細", "").strip()
        supervisor = row[3].strip()
        try:
            perf_val = int(row[10].replace(',', ''))
        except:
            continue

        if name == supervisor:
            # Task 1: 單位狀態 (主管) - 區分達標與未達標
            if mode in ["all", "warning"]:
                if perf_val >= 30000:
                    mem_key = f"{name}_mgr_pass"
                    if mem_key not in memory["sent_names"]:
                        # 達標：綠色勾勾，拿掉「主管」字眼
                        res["manager_passed"].append(f"✅ {name} 累積業績 {perf_val:,} 元")
                        memory["sent_names"].append(mem_key)
                else:
                    mem_key = f"{name}_mgr_warn"
                    if mem_key not in memory["sent_names"]:
                        # 未達標：警告符號
                        res["manager_warnings"].append(f"⚠️ {name} 累積業績 {perf_val:,} 元 (未達3萬)")
                        memory["sent_names"].append(mem_key)
        else:
            # Task 2 & 3: 職員賀報 (換成 ㊗️ 與換行格式)
            if mode in ["all", "congrats"]:
                if perf_val >= 100000:
                    mem_key = f"{name}_10w"
                    if mem_key not in memory["sent_names"]:
                        # 10萬大關專屬文字
                        res["congrats"].append(f"㊗️ {name} 突破 10 萬大關！\n累積：{perf_val:,}")
                        res["big_congrats_raw"].append({"name": name, "fyc": perf_val})
                        memory["sent_names"].append(mem_key)
                elif perf_val >= 30000:
                    mem_key = f"{name}_3w"
                    if mem_key not in memory["sent_names"]:
                        # 3萬富邦之星文字
                        res["congrats"].append(f"㊗️ {name} 達成富邦之星！\n累積：{perf_val:,}")
                        res["congrats_raw"].append({"name": name, "fyc": perf_val})
                        memory["sent_names"].append(mem_key)

    # 不論是警告還是賀報，只要有檢查，就存回記憶體
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

def task_salary_top10(bot):
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
    # 步驟四：排序並回傳前 10 名
    # ==========================================
    salaries.sort(reverse=True)
    return salaries[:10]

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
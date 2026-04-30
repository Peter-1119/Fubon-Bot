# payloads.py
import json
import urllib.parse
import re
from datetime import datetime
from config import get_dynamic_dates

def get_dynamic_work_month(bot):
    """內部輔助函式：動態取得最新的工作月 ID"""
    print("[系統] 正在請求 InitUnitList 以動態取得最新工作月 ID...")
    
    # 觸發用的 Payload (故意將 workMonth 留空)
    payload = {
        "Unit0": "BMMBX-0000",
        "Type1": "1076",
        "Type2": "1",
        "target": "Unit1"
    }
    
    response_text = bot.fetch_api_data("/SAVLife/Item0028/InitUnitList", payload)
    
    try:
        json_arr = json.loads(response_text)
        target_str = ""
        for item in json_arr:
            if isinstance(item, str) and "workMonth==" in item:
                target_str = item
                break
        
        if not target_str:
            print("[警告] 回應中找不到 workMonth== 欄位，伺服器可能更改了邏輯。")
            return "1725" # 備用預設值
            
        decoded_string = urllib.parse.unquote(target_str)
        match = re.search(r'workMonth==\s*(\d+)\|', decoded_string)
        
        if match:
            current_month_id = match.group(1)
            print(f"[成功] 🎯 抓到本月最新工作月 ID: {current_month_id}")
            return current_month_id
        else:
            print("[警告] 正則表達式匹配失敗。")
            return "1725" # 備用預設值
            
    except Exception as e:
        print(f"[錯誤] 動態月份解析失敗: {e}")
        return "1725"

# ==========================================
# 以下為各項任務的 Payload 產生器
# ==========================================

def get_performance_params(bot):
    """Task 1, 2, 3: 取得受理業績查詢參數 (需要 bot 來動態抓取月份)"""
    dates = get_dynamic_dates()
    dynamic_work_month_id = get_dynamic_work_month(bot) # 呼叫上方函式
    
    return {
        "Type3": "1",
        "Unit1": "BMMB1-0000",
        "Unit2": "TPU03-0000",
        "Unit3": "TP097-0000",
        "Unit2_Text": "ＴＰＵ０３北三區部",
        "Unit3_Text": "富悅通訊處",
        "Agent_Text": "全部",
        "View_flag": "_II",
        "Type1": "1076",
        "Unit4": "",
        "Unit4_Text": "",
        "Unit_info": "",
        "UnitCode": "M122758417",
        "RaceItem": "1",
        "Detail": "N",
        "WorkMonth": dynamic_work_month_id, # 動態帶入
        "CalDate": dates["TODAY_YYYYMMDD"], # 動態帶入當天日期
        "IsLockYm": "N",
        "BusType": "1",
        "RdoRaceName": "個人業績",
        "PageCode": "AcceptResultAgent",
        "TagId": "ListPage5-0",
        "Target": "#ListPage-5-0"
    }

def get_attendance_params():
    """Task 4: 取得出缺席參數"""
    return {
        "QueryType": "unit",
        "Unit2": "TPU03-0000",
        "Unit3": "TP097-0000",
        "QueryInterval": "0",
        "Unit3_Text": "富悅通訊處",
        "TagId": "Panel1",
        "OrderBy": "預設",
        "OrderDir": "ASC",
        "PageSize": "40",
        "CurrentPage": "1",
        "searchType": "1",
        "Target": "#MainPart > div[main=01] #ListPage1-Panel1"
    }

def get_yearly_bonus_params():
    """Task 6: 取得年終資料參數"""
    return {
        "Unit3": "TP097-0000",
        "TagId": "ListPage",
        "Target": "#MainPart > div[main=01] #ListPage-panel",
        "OrderBy": "營管單位名稱",
        "OrderDir": "DESC",
        "PageSize": "40",
        "CurrentPage": "1"
    }

def get_salary_params(agent_id, query_date):
    """Task 5: 取得特定員工薪資參數"""
    return {
        "Agent": agent_id,
        "QueryReleaseDate": query_date, # 例如 "115/04/25"
        "TagId": "ListPage"
    }

def get_short_term_performance_params():
    """短期業績參數"""
    return {
        "Unit1": "BMMB1-0000",
        "Unit2": "TPU03-0000",
        "Unit3": "TP097-0000",
        "Unit4": "",
        "Agent": "",
        "RaceItem": "Short005",
        "PerformanceItem": "1",
        "SubmitMode": "",
        "Unit3_Text": "富悅通訊處",
        "PerformanceItem_Text": "個人業績",
        "TagId": "Panel1",
        "Target": "#MainPart > div[main=01] #ListPage1-Panel1"
    }

def get_long_term_performance_params():
    """長期業績參數 (MDRT/IDA)"""
    return {
        "ChannelType": "unit0",
        "Unit1": "BMMB1-0000",
        "Unit2": "TPU03-0000",
        "Unit3": "TP097-0000",
        "Agent": "",
        "YearKind": "115", # 若需動態可改由 config 取得
        "RaceName": "MDRT暨IDA",
        "onlyModel": "false",
        "func": "Query",
        "TagId": "ListPage",
        "Target": "#MainPart > div[main=01] #ListPage"
    }
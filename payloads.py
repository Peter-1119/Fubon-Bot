# payloads.py
from config import get_dynamic_dates

# 共用基底：全台灣幾萬個通訊處，你的程式碼只需要改這裡就能換通訊處！
BASE_PARAMS = {
    "Unit0": "BMMBX-0000", "Unit1": "BMMB1-0000", "Unit2": "TPU03-0000", "Unit3": "TP097-0000",
    "Unit0_Text": "業務通路", "Unit1_Text": "第一營業管理", "Unit2_Text": "ＴＰＵ０３北三區部", "Unit3_Text": "富悅通訊處",
    "Unit4": "", "Unit4_Text": "", "Unit_info": "", "Func": "Query"
}

def get_performance_params():
    """Task 1, 2, 3: 取得受理業績查詢參數"""
    dates = get_dynamic_dates() # <--- 關鍵！在這裡拿時間
    
    p = BASE_PARAMS.copy()
    p.update({
        "Type3": "1", "Agent_Text": "全部", "View_flag": "_II", "Type1": "1076",
        "UnitCode": "M122758417", "RaceItem": "1", "Detail": "N", 
        "WorkMonth": "1720", # 注意：工作月代碼可能也要動態抓取，這視系統邏輯而定
        "CalDate": dates["TODAY_YYYYMMDD"],
        "IsLockYm": "N", "BusType": "1", "RdoRaceName": "個人業績",
        "PageCode": "AcceptResultAgent", "TagId": "ListPage5-0", "Target": "#ListPage-5-0"
    })
    return p

def get_attendance_params():
    """Task 4: 取得出缺席參數"""
    p = BASE_PARAMS.copy()
    p.update({
        "QueryType": "unit", "ChannelType": "self", "Agent": "", "QueryInterval": "0",
        "QueryType_Text": "通訊處", "Agent_Text": "", "QueryInterval_Text": "當日",
        "TagId": "Panel1", "OrderBy": "預設", "OrderDir": "ASC", "PageSize": "40",
        "CurrentPage": "1", "searchType": "1", "Target": "#MainPart > div[main=01] #ListPage1-Panel1",
        "unit3options": "TP097-0000"
    })
    return p

def get_personal_list_params():
    """獲取薪資名單用"""
    dates = get_dynamic_dates()
    p = BASE_PARAMS.copy()
    p.update({
        "ChannelType": "self", "Unit4": "", "Agent": "",
        "QueryReleaseDate": dates["TODAY_ROC"], # 動態日期
        "Unit4_Text": "", "Agent_Text": "", "SelectTitleType": "", "Self": "true", "target": "Agent"
    })
    return p

def get_salary_params(agent_id, agent_name):
    """Task 5: 取得特定員工薪資參數"""
    dates = get_dynamic_dates()
    p = BASE_PARAMS.copy()
    p.update({
        "ChannelType": "unit0", "Unit4": "",
        "Agent": agent_id, "Agent_Text": agent_name,
        "QueryReleaseDate": dates["SALARY_QUERY_DATE"],
        "Unit4_Text": "", "TagId": "ListPage", "Target": "#MainPart > div[main=01]"
    })
    return p

def get_yearly_bonus_params():
    """Task 6: 取得年終資料參數"""
    p = BASE_PARAMS.copy()
    p.update({
        "QueryType": "team", "ChannelType": "self", "Agent": "", "ConditionTags": "",
        "QueryType_Text": "業務主管", "Agent_Text": "全部", "onlyModel": "false",
        "promoteAg": "", "ThisReportType": "A", "CurrId": "1", "TagId": "ListPage",
        "Target": "#MainPart > div[main=01] #ListPage-panel", "OrderBy": "營管單位名稱",
        "OrderDir": "DESC", "PageSize": "40", "CurrentPage": "1", "Func": "FYCBonusInfo"
    })
    return p
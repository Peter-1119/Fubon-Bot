import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

LINE_TOKEN = os.getenv("LINE_CHANNEL_TOKEN")
SETUP_PASSWORD = os.getenv("SETUP_PASSWORD", "fubon888")

def get_dynamic_dates():
    now = datetime.now()
    roc_year = str(now.year - 1911)
    
    return {
        "TODAY_YYYYMMDD": now.strftime("%Y%m%d"),
        "TODAY_ROC": f"{roc_year}/{now.strftime('%m/%d')}",
        "SALARY_QUERY_DATE": f"{roc_year}/{now.strftime('%m')}/25"
    }
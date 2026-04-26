# core/parsers.py
import re
import urllib.parse
from bs4 import BeautifulSoup

def decode_asp_html(encoded_str):
    """將 %uXXXX 轉回中文，並將 %XX 轉回 HTML 標籤"""
    decoded = re.sub(r'%u([0-9a-fA-F]{4})', lambda m: chr(int(m.group(1), 16)), encoded_str)
    return urllib.parse.unquote(decoded)

def parse_agent_list(payload_str):
    """解析 InitUnitList 回傳的業務員名單"""
    decoded_text = decode_asp_html(payload_str)
    agents_dict = {}
    if "Agent==" in decoded_text:
        core_data = decoded_text.split("Agent==")[1].split("\nselect")[0]
        sections = core_data.split('\n')
        # 加上防呆機制，確保長度一致才 zip
        ids = [i for i in sections[0].split('\r') if i.strip()]
        names = [n for n in sections[1].split('\r') if n.strip() and n != "請選擇"]
        agents_dict = dict(zip(ids[-len(names):], names))
    return agents_dict

def extract_table_data(html_string, target_class='report-table', table_index=0):
    """通用的表格擷取器，回傳二維陣列 (List of Lists)"""
    if not html_string:
        return []
        
    soup = BeautifulSoup(html_string, 'html.parser')
    tables = soup.find_all('table', class_=target_class)
    
    if not tables:
        tables = soup.find_all('table')
        
    if len(tables) > table_index:
        table = tables[table_index]
        rows = table.find('tbody').find_all('tr') if table.find('tbody') else table.find_all('tr')[1:]
        
        result_data = []
        for r in rows:
            cells = [td.get_text(strip=True) for td in r.find_all('td')]
            if cells:
                result_data.append(cells)
        return result_data
    return []
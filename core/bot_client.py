import os, requests, base64, json, time, re, pickle
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
import urllib.parse

from core.captcha import SimpleCaptchaSolver
from core.parsers import decode_asp_html

class FubonAutoBot:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            "Connection": "keep-alive"
        })
        self.base_url = "https://magent.fubonlife.com.tw"
        self.csrf_token = "" 
        self.solver = SimpleCaptchaSolver()
        
    def _encrypt_payload(self, data_dict):
        if not data_dict:
            text_to_encrypt = "{}"
        else:
            text_to_encrypt = json.dumps(data_dict, separators=(',', ':'))
            
        key = b"8080808080808080"
        iv  = b"8080808080808080"
        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(text_to_encrypt.encode('utf-8'), AES.block_size)
        encrypted_bytes = cipher.encrypt(padded_data)
        encrypted_base64 = base64.b64encode(encrypted_bytes).decode('utf-8')
        return urllib.parse.quote(encrypted_base64, safe='*@-_+./')

    def _post_sys_exec(self, endpoint, vars_dict, tags_dict=None):
        if tags_dict is None:
            tags_dict = {}

        # 模擬 JS 型別轉換
        def _js_transform(d):
            res = {}
            for k, v in d.items():
                if v is None: res[k] = ""
                elif isinstance(v, (dict, list)): res[k] = json.dumps(v, separators=(',', ':'))
                elif isinstance(v, bool): res[k] = str(v).lower()
                else: res[k] = str(v)
            return res

        url = f"{self.base_url}{endpoint}"
        data = {
            "__RequestVerificationToken": self.csrf_token,
            "_vars": self._encrypt_payload(_js_transform(vars_dict)),
            "_tags": self._encrypt_payload(_js_transform(tags_dict))
        }
        
        api_headers = {
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://magent.fubonlife.com.tw",
            "Referer": "https://magent.fubonlife.com.tw/SAVLife/Login",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
        }
        return self.session.post(url, data=data, headers=api_headers)

    def get_captcha_and_solve(self):
        """【自動化核心】下載圖片並交給 OpenCV 辨識"""
        print("[系統] 0.5 正在獲取動態驗證碼...")
        timestamp = int(time.time() * 1000)
        captcha_url = f"{self.base_url}/SAVLife/Login/IdentifyCode?t={timestamp}" 
        
        img_headers = {
            "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
            "Referer": "https://magent.fubonlife.com.tw/SAVLife/Login"
        }
        resp = self.session.get(captcha_url, headers=img_headers)
        
        # 直接把圖片的 byte array 丟給解碼器，秒解！
        captcha_code = self.solver.solve_from_bytes(resp.content)
        print(f"[系統] 🤖 機器視覺辨識結果: {captcha_code}")
        
        return captcha_code

    def save_cookies(self, filename="fubon_cookies.pkl"):
        with open(filename, 'wb') as f:
            pickle.dump(self.session.cookies, f)
        print("[系統] 💾 成功將 Cookies 儲存至本地快取！")

    def load_cookies(self, filename="fubon_cookies.pkl"):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                self.session.cookies.update(pickle.load(f))
            print("[系統] 📂 成功讀取本地 Cookies 快取！")
            return True
        return False

    def is_logged_in(self):
        print("[系統] 🔍 測試目前 Token 是否有效...")
        test_resp = self.session.get(f"{self.base_url}/SAVLife/NHome", allow_redirects=False)
        if test_resp.status_code == 302 and "Login" in test_resp.headers.get('Location', ''):
            print("[警告] ❌ Token 已過期，準備重新登入。")
            return False
        print("[成功] ✅ Token 依然有效！可以直接抓報表。")
        return True
    
    def execute_login(self, username, password):
        import re
        
        # 0. 建立 Session 並擷取指紋
        print("[系統] 0. 建立 Session 並擷取防護指紋...")
        login_resp = self.session.get(f"{self.base_url}/SAVLife/Login")
        html_text = login_resp.text
        
        info_match = re.search(r'var\s+info\s*=\s*\[(.*?)\];', html_text, re.DOTALL)
        if info_match:
            strings = re.findall(r'"([^"]*)"', info_match.group(1))
            if len(strings) >= 4:
                sys_token, sys_code, sys_ip = strings[0], strings[1], strings[2]
            else:
                sys_token, sys_code, sys_ip = self.session.cookies.get("ASP.NET_SessionId", ""), "20", "127.0.0.1"
        else:
            sys_token, sys_code, sys_ip = self.session.cookies.get("ASP.NET_SessionId", ""), "20", "127.0.0.1"

        target_url = "/exc/to_fbsso.asp?ContrastID=SSO2SAV2"
        app_version = self.session.headers["User-Agent"].replace("Mozilla/", "")
        dynamic_info_array = [sys_token, target_url, sys_code, sys_ip, sys_ip, app_version]

        # 1. 拿驗證碼並校驗 (現在是全自動了)
        captcha_code = self.get_captcha_and_solve()
        if captcha_code == "ERROR" or len(captcha_code) != 4:
            print("[失敗] 驗證碼辨識異常。")
            return False
            
        print("[系統] 1. 預先校驗驗證碼...")
        check_resp = self._post_sys_exec("/SAVLife/Login/CheckIdentifyCode", {"VerificationCode": captcha_code})
        if "true" not in check_resp.text.lower():
            print(f"[失敗] 驗證碼錯誤: {check_resp.text}")
            return False
        print("[成功] 驗證碼校驗通過！")

        time.sleep(0.5)

        # 2. 執行 LoginCheck
        print("[系統] 2. 執行 LoginCheck...")
        login_check_payload = {
            "AgentID": username, "Pwd": password, "VerificationCode": captcha_code,
            "loginType": 0, "Info": dynamic_info_array
        }
        lcheck_resp = self._post_sys_exec("/SAVLife/Login/LoginCheck", login_check_payload)
        
        server_auth_data = {}
        try:
            resp_data = lcheck_resp.json()
            if "d" in resp_data:
                inner_json = json.loads(resp_data["d"])
                if inner_json.get("IsOK") == True:
                    print("[成功] LoginCheck 身份驗證通過！")
                    server_auth_data["ID"] = inner_json.get("ID", username)
                    server_auth_data["O365Login"] = inner_json.get("Key", "")
                    server_auth_data["IsAgent"] = inner_json.get("IsAgent", "Y")
                    server_auth_data["System"] = inner_json.get("System", "1")
                    server_auth_data["IsOfficeStart"] = inner_json.get("IsOfficeStart", "00")
                    server_auth_data["EmailAddr"] = inner_json.get("EmailAddr", "")
                    server_auth_data["MobPhoneNo"] = inner_json.get("MobPhoneNo", "")
                else:
                    print(f"[失敗] LoginCheck 拒絕: {inner_json.get('Message')}")
                    return False
        except Exception as e:
            print(f"[失敗] LoginCheck 解析錯誤: {lcheck_resp.text}")
            return False

        # 3. 查詢業務員狀態
        print("[系統] 3. 查詢業務員狀態 (QryAgent)...")
        real_id = server_auth_data.get("ID", username)
        qry_resp = self._post_sys_exec("/SAVLife/Login/QryAgent", {"agentId": real_id})
        
        agent_name = ""
        try:
            qry_list = qry_resp.json()
            if isinstance(qry_list, list) and len(qry_list) > 1 and "agent" in qry_list[1]:
                agent_name = json.loads(qry_list[1]["agent"]).get("AgentName", "")
        except Exception:
            pass

        # 4. 最終 Login
        print("[系統] 4. 送出最終 Login 授權...")
        final_login_payload = {
            "Act": "Login", "PopupFlag": "0", "ID": real_id, "Pwd": password,
            "IsAgent": server_auth_data.get("IsAgent"), "IsOfficeStart": server_auth_data.get("IsOfficeStart"),
            "O365Login": server_auth_data.get("O365Login"), "EmailAddr": server_auth_data.get("EmailAddr"),
            "MobPhoneNo": server_auth_data.get("MobPhoneNo"), "System": server_auth_data.get("System"),
            "AgentName": agent_name, "RemberAcctNo": username, "txtInput": "",
            "imageId": "Image11", "imageStatus": "1", "contrastID": "SSO2SAV",
            "url": target_url, "act2": "0", "VerificationCode": captcha_code,
            "Remember": "", "question": "", "answer": "", "defaultPwd": "",
            "agentName": "", "action": "", "enableAgentMail": "",
            "osName": "Windows", "browserName": "Chrome"
        }
        
        final_resp = self._post_sys_exec("/SAVLife/Login/Login", final_login_payload)
        
        if '""' in final_resp.text or "ok" in final_resp.text.lower() or final_resp.text == "[]":
            print("\n[大成功] 🎉 所有安全防護皆已破解！Session 已取得最高權限！")
            return True
        else:
            print(f"[失敗] 最終 Login 失敗: {final_resp.text[:500]}")
            return False
        
    def fetch_api_raw_string(self, endpoint, payload):
        """專門用來獲取 InitUnitList 這種非 HTML 的原始字串"""
        resp = self._post_sys_exec(endpoint, payload)
        try:
            json_data = resp.json()
            for item in json_data:
                if isinstance(item, str) and "Agent==" in item:
                    return item
        except Exception as e:
            print(f"解析 JSON 失敗: {e}")
        return ""

    def fetch_api_html(self, endpoint, payload):
        """
        發送 API 請求，解開 JSON 並回傳乾淨的 HTML "字串" (非 Soup 物件)
        """
        tags_dict = {} 
        resp = self._post_sys_exec(endpoint, payload, tags_dict=tags_dict)
        
        if resp.status_code != 200:
            print(f"[失敗] 伺服器回傳狀態碼: {resp.status_code}")
            return None
        if not resp.text.strip():
            print("[失敗] 伺服器回傳了空內容。")
            return None

        try:
            json_data = resp.json()
            for item in json_data:
                if isinstance(item, str) and "==" in item:
                    _, encoded_html = item.split("==", 1)
                    # 呼叫 parsers.py 裡面的解碼器
                    pure_html_string = decode_asp_html(encoded_html)
                    return pure_html_string # <--- 只回傳字串！
            
            print("[警告] JSON 解析成功，但裡面找不到 HTML。")
        except Exception as e:
            print(f"[錯誤] JSON 解析失敗: {e}")
            
        return None

    def fetch_api_data(self, endpoint, payload):
        """
        最純粹的 API 請求，專門用來抓取未經處理的原始回應字串。
        適用於分析 InitUnitList 等含有亂碼指令的封包。
        """
        resp = self._post_sys_exec(endpoint, payload)
        if resp.status_code != 200:
            print(f"[失敗] 伺服器回傳狀態碼: {resp.status_code}")
            return "[]"
            
        return resp.text
    
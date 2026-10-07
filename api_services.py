# api_services.py
import requests
import pandas as pd
import streamlit as st
import re

# 從 Streamlit 雲端的 Secrets 安全讀取金鑰 (若本機測試則讀取預設防呆)
try:
    TDX_CLIENT_ID = st.secrets["TDX_CLIENT_ID"]
    TDX_CLIENT_SECRET = st.secrets["TDX_CLIENT_SECRET"]
    GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
except:
    # 這裡放你本機測試用的預設值 (注意：上傳到 GitHub 前請確保不要外洩真實金鑰，或本機直接用 secrets.toml)
    TDX_CLIENT_ID = '請填寫你的TDX_CLIENT_ID金鑰'
    TDX_CLIENT_SECRET = '請填寫你的TDX_CLIENT_SECRET金鑰'
    GOOGLE_MAPS_API_KEY = '請填寫你的GOOGLE_MAPS_API金鑰'

@st.cache_data(ttl=3000)
def get_tdx_token():
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    data = {'grant_type': 'client_credentials', 'client_id': TDX_CLIENT_ID, 'client_secret': TDX_CLIENT_SECRET}
    try:
        res = requests.post(auth_url, data=data, timeout=3)
        if res.status_code == 200: return res.json().get('access_token')
    except: pass
    return None

def get_real_bus_eta(token, route_name, stop_keyword):
    if not token: return "預估 5"
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Hsinchu/{route_name}?$format=JSON"
    headers = {'authorization': f'Bearer {token}'}
    try:
        res = requests.get(url, headers=headers, timeout=3)
        if res.status_code == 200:
            for item in res.json():
                stop_name = item.get("StopName", {}).get("Zh_tw", "")
                if stop_keyword in stop_name and "EstimateTime" in item:
                    wait_mins = int(item["EstimateTime"]) // 60
                    return f"即時 {wait_mins}" if wait_mins > 0 else "即將進站"
            return "未發車"
    except: pass
    return "預估 8"

def clean_html(raw_html):
    return re.sub(r'<.*?>', '', raw_html)

def get_google_transit_route(start_loc, dest_loc):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請填寫你的GOOGLE_MAPS_API金鑰':
        return {"status": "error", "message": "尚未設定 Google API 金鑰！"}

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"台灣新竹市 {start_loc}",
        "destination": f"台灣新竹市 {dest_loc}",
        "mode": "transit",
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        
        if data.get("status") == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            real_fare = route.get("fare", {}).get("value", 15)
            total_duration = leg["duration"]["text"]
            
            transit_legs = []
            path_coords = []
            has_bus = False
            
            for step in leg["steps"]:
                path_coords.append({"lat": step["start_location"]["lat"], "lon": step["start_location"]["lng"]})
                
                if step["travel_mode"] == "TRANSIT":
                    has_bus = True
                    details = step["transit_details"]
                    bus_name = details["line"].get("short_name", details["line"].get("name"))
                    board = details["departure_stop"]["name"]
                    alight = details["arrival_stop"]["name"]
                    num_stops = details.get("num_stops", 0)
                    dep_time = details.get("departure_time", {}).get("text", "未提供")
                    
                    transit_legs.append({
                        "type": "TRANSIT",
                        "bus_name": bus_name, "board": board, 
                        "alight": alight, "num_stops": num_stops,
                        "dep_time": dep_time, "duration": step["duration"]["text"]
                    })
                elif step["travel_mode"] == "WALKING":
                    instruction = clean_html(step.get("html_instructions", "步行"))
                    transit_legs.append({
                        "type": "WALKING",
                        "instruction": instruction,
                        "duration": step["duration"]["text"]
                    })
                    
            path_coords.append({"lat": leg["end_location"]["lat"], "lon": leg["end_location"]["lng"]})
            coords_df = pd.DataFrame(path_coords)
            
            if not has_bus:
                return {"status": "not_found", "message": "此距離過近或無大眾運輸直達，建議直接步行前往！"}
            
            eta = "無動態"
            for t in transit_legs:
                if t["type"] == "TRANSIT":
                    token = get_tdx_token()
                    eta = get_real_bus_eta(token, t["bus_name"], t["board"][:2])
                    break
                
            return {
                "status": "success", "transit_legs": transit_legs, 
                "eta": eta, "travel_time": total_duration, 
                "coords": coords_df, "fare": real_fare
            }
        else:
            return {"status": "not_found", "message": f"找不到大眾運輸路線，請嘗試距離較遠的地點"}
    except Exception as e:
        return {"status": "error", "message": f"連線錯誤: {e}"}
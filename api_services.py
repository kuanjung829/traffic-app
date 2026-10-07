# api_services.py
import requests
import pandas as pd
import streamlit as st

# ==========================================
# API 金鑰設定
# ==========================================
TDX_CLIENT_ID = 'kuanjung829-5b32ef80-7be0-4ebe'
TDX_CLIENT_SECRET = '98aa31ee-f7d1-408c-af85-8d1887791ad9'
GOOGLE_MAPS_API_KEY = '請貼上你的GOOGLE_MAPS_API金鑰' 

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

def get_google_transit_route(start_loc, dest_loc):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請貼上你的GOOGLE_MAPS_API金鑰':
        return {"status": "error", "message": "請先填寫 Google API 金鑰！"}

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
            route = data["routes"][0]["legs"][0]
            start_coord = route["start_location"]
            end_coord = route["end_location"]
            total_duration = route["duration"]["text"]
            
            transit_legs = []
            for step in route["steps"]:
                if step["travel_mode"] == "TRANSIT":
                    details = step["transit_details"]
                    bus_name = details["line"].get("short_name", details["line"].get("name"))
                    board = details["departure_stop"]["name"]
                    alight = details["arrival_stop"]["name"]
                    num_stops = details.get("num_stops", 0)
                    transit_legs.append({
                        "bus_name": bus_name, "board": board, 
                        "alight": alight, "num_stops": num_stops
                    })
            
            if transit_legs:
                first_bus = transit_legs[0]
                token = get_tdx_token()
                eta = get_real_bus_eta(token, first_bus["bus_name"], first_bus["board"][:2]) 
                
                coords_df = pd.DataFrame([
                    {"lat": start_coord["lat"], "lon": start_coord["lng"], "name": f"起點：{start_loc}"},
                    {"lat": end_coord["lat"], "lon": end_coord["lng"], "name": f"終點：{dest_loc}"}
                ])
                
                return {
                    "status": "success", "transit_legs": transit_legs, 
                    "eta": eta, "travel_time": total_duration, 
                    "coords": coords_df, "fare": 15 * len(transit_legs)
                }
            else:
                return {"status": "not_found", "message": "這段路程建議直接步行，無需搭車！"}
        else:
            return {"status": "not_found", "message": f"找不到大眾運輸路線 ({data.get('status')})"}
    except Exception as e:
        return {"status": "error", "message": f"連線錯誤: {e}"}
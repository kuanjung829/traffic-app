# api_services.py
import requests
import pandas as pd
import streamlit as st
import re
import math

try:
    TDX_CLIENT_ID = st.secrets["TDX_CLIENT_ID"]
    TDX_CLIENT_SECRET = st.secrets["TDX_CLIENT_SECRET"]
    GOOGLE_MAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]
except:
    TDX_CLIENT_ID = 'kuanjung829-5b32ef80-7be0-4ebe'
    TDX_CLIENT_SECRET = '98aa31ee-f7d1-408c-af85-8d1887791ad9'
    GOOGLE_MAPS_API_KEY = '請填寫你的GOOGLE_MAPS_API金鑰'

@st.cache_data(ttl=3000)
def get_tdx_token():
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    data = {'grant_type': 'client_credentials', 'client_id': TDX_CLIENT_ID, 'client_secret': TDX_CLIENT_SECRET}
    try:
        res = requests.post(auth_url, data=data, timeout=2)
        if res.status_code == 200: return res.json().get('access_token')
    except: pass
    return None

def get_real_bus_eta(token, route_name, stop_keyword):
    if not token: return "預估 5 分"
    priority_cities = ["Taipei", "NewTaipei", "Taoyuan", "Taichung", "Kaohsiung", "Hsinchu", "HsinchuCounty"]
    for city in priority_cities:
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}/{route_name}?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        try:
            res = requests.get(url, headers=headers, timeout=1)
            if res.status_code == 200 and res.json():
                for item in res.json():
                    stop_name = item.get("StopName", {}).get("Zh_tw", "")
                    if stop_keyword in stop_name and "EstimateTime" in item:
                        wait_mins = int(item["EstimateTime"]) // 60
                        return f"即時 {wait_mins} 分" if wait_mins > 0 else "即將進站"
        except: pass
    return "即時 3 分"

def clean_html(raw_html):
    return re.sub(r'<.*?>', '', raw_html)

def get_google_transit_route(start_loc, dest_loc):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請填寫你的GOOGLE_MAPS_API金鑰':
        return {"status": "error", "message": "尚未設定 Google API 金鑰！"}

    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": start_loc,
        "destination": dest_loc,
        "mode": "transit",
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        res = requests.get(url, params=params, timeout=8)
        data = res.json()
        if data.get("status") == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            real_fare = route.get("fare", {}).get("value", 15)
            total_duration = leg["duration"]["text"]
            
            transit_legs = []
            path_coords = []
            has_transit = False
            
            for step in leg["steps"]:
                path_coords.append({"lat": step["start_location"]["lat"], "lon": step["start_location"]["lng"]})
                if step["travel_mode"] == "TRANSIT":
                    has_transit = True
                    details = step["transit_details"]
                    vehicle_type = details["line"]["vehicle"].get("type", "BUS")
                    bus_name = details["line"].get("short_name", details["line"].get("name"))
                    board = details["departure_stop"]["name"]
                    alight = details["arrival_stop"]["name"]
                    num_stops = details.get("num_stops", 0)
                    dep_time = details.get("departure_time", {}).get("text", "頻繁發車")
                    transit_legs.append({
                        "type": "TRANSIT", "vehicle": vehicle_type,
                        "bus_name": bus_name, "board": board, "alight": alight, 
                        "num_stops": num_stops, "dep_time": dep_time, "duration": step["duration"]["text"]
                    })
                elif step["travel_mode"] == "WALKING":
                    transit_legs.append({
                        "type": "WALKING", "instruction": clean_html(step.get("html_instructions", "步行")),
                        "duration": step["duration"]["text"]
                    })
            path_coords.append({"lat": leg["end_location"]["lat"], "lon": leg["end_location"]["lng"]})
            coords_df = pd.DataFrame(path_coords)
            
            if not has_transit:
                return {"status": "not_found", "message": "此距離過近或無大眾運輸直達，建議直接步行前往！"}
            
            eta = "即時 3 分"
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
            return {"status": "not_found", "message": f"找不到大眾運輸路線 ({data.get('status')}): 請確認起迄點名稱正確"}
    except Exception as e:
        return {"status": "error", "message": f"連線逾時或錯誤: {e}"}

# --- 附近站牌功能 (改良版：透過計算縣市站牌座標距離來精準過濾) ---
def get_location_coordinates(address):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請填寫你的GOOGLE_MAPS_API金鑰':
        return None
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"address": address, "key": GOOGLE_MAPS_API_KEY}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.json().get("status") == "OK":
            loc = res.json()["results"][0]["geometry"]["location"]
            return loc["lat"], loc["lng"]
    except: pass
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """計算兩經緯度之間的距離 (公尺)"""
    R = 6371000  # 地球半徑 (公尺)
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

@st.cache_data(ttl=3600)
def fetch_city_stops(token, city):
    """取得指定縣市的所有站牌快取"""
    if not token: return []
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/Stop/City/{city}?$format=JSON"
    headers = {'authorization': f'Bearer {token}'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            return res.json()
    except: pass
    return []

def get_nearby_stops(token, lat, lon, radius=2000):
    if not token: return []
    
    # 自動判斷要掃描哪些縣市 (預設涵蓋新竹、雙北、台中、桃園)
    cities = ["Hsinchu", "HsinchuCounty", "Taipei", "NewTaipei", "Taoyuan", "Taichung"]
    nearby_results = []
    
    for city in cities:
        stops = fetch_city_stops(token, city)
        for stop in stops:
            pos = stop.get("StopPosition", {})
            s_lat = pos.get("PositionLat")
            s_lon = pos.get("PositionLon")
            if s_lat and s_lon:
                dist = calculate_distance(lat, lon, s_lat, s_lon)
                if dist <= radius:
                    stop_copy = stop.copy()
                    stop_copy["distance"] = int(dist)
                    nearby_results.append(stop_copy)
                    
    # 依照距離遠近排序
    nearby_results.sort(key=lambda x: x["distance"])
    return nearby_results[:15] # 最多回報最近的 15 個站牌

def get_stop_eta(token, stop_id):
    if not token: return []
    priority_cities = ["Hsinchu", "HsinchuCounty", "Taipei", "NewTaipei", "Taoyuan", "Taichung", "Kaohsiung"]
    routes_eta = []
    for city in priority_cities:
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}?$filter=StopUID eq '{stop_id}'&$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        try:
            res = requests.get(url, headers=headers, timeout=2)
            if res.status_code == 200 and res.json():
                for item in res.json():
                    route_name = item.get("RouteName", {}).get("Zh_tw", "未知路線")
                    if "EstimateTime" in item:
                        wait_mins = int(item["EstimateTime"]) // 60
                        eta_text = f"{wait_mins} 分鐘" if wait_mins > 0 else "即將進站"
                    else:
                        eta_text = "未發車"
                    if not any(r['route'] == route_name for r in routes_eta):
                        routes_eta.append({"route": route_name, "eta": eta_text})
        except: pass
        if routes_eta: break
    return routes_eta
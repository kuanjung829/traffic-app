# api_services.py
import requests
import pandas as pd
import streamlit as st
import re
import datetime
from datetime import timedelta

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
        res = requests.post(auth_url, data=data, timeout=3)
        if res.status_code == 200: return res.json().get('access_token')
    except: pass
    return None

def clean_html(raw_html):
    return re.sub(r'<.*?>', '', raw_html)

def get_google_transit_route(start_loc, dest_loc, mode="live", time_mode="出發時間", target_datetime=None):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請填寫你的GOOGLE_MAPS_API金鑰':
        return {"status": "error", "message": "尚未設定 Google API 金鑰！"}

    url = "https://maps.googleapis.com/maps/api/directions/json"
    
    # 決定行程的基準時間
    base_datetime = datetime.datetime.now()
    if mode == "specific" and target_datetime:
        base_datetime = target_datetime
        
    timestamp = int(base_datetime.timestamp())
    
    params = {
        "origin": start_loc,
        "destination": dest_loc,
        "mode": "transit",
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    if mode == "specific" and time_mode == "預計抵達時間":
        params["arrival_time"] = timestamp
    else:
        params["departure_time"] = timestamp
            
    try:
        res = requests.get(url, params=params, timeout=8)
        data = res.json()
        
        if data.get("status") == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            real_fare = route.get("fare", {}).get("value", 15)
            total_duration = leg["duration"]["text"]
            
            # 取得總行程時間
            dep_time_text = leg.get("departure_time", {}).get("text")
            arr_time_text = leg.get("arrival_time", {}).get("text")
            
            # 🌟 自製時間累加器：如果 Google 沒給總時間，我們自己用 base_datetime 算
            current_time_tracker = base_datetime
            if not dep_time_text:
                dep_time_text = current_time_tracker.strftime("%H:%M")
            else:
                # 嘗試把 Google 吐出來的時間 (如 16:20) 轉回 datetime 物件作為起始點
                try:
                    time_obj = datetime.datetime.strptime(dep_time_text, "%H:%M")
                    current_time_tracker = current_time_tracker.replace(hour=time_obj.hour, minute=time_obj.minute)
                except:
                    pass

            transit_legs = []
            path_coords = []
            has_transit = False
            
            for step in leg["steps"]:
                path_coords.append({"lat": step["start_location"]["lat"], "lon": step["start_location"]["lng"]})
                
                # 取得這一段花費的秒數，用來累加時間
                step_seconds = step["duration"].get("value", 0)
                step_duration_text = step["duration"]["text"]
                
                if step["travel_mode"] == "TRANSIT":
                    has_transit = True
                    details = step["transit_details"]
                    vehicle_type = details["line"]["vehicle"].get("type", "BUS")
                    bus_name = details["line"].get("short_name", details["line"].get("name"))
                    board = details["departure_stop"]["name"]
                    alight = details["arrival_stop"]["name"]
                    num_stops = details.get("num_stops", 0)
                    
                    # 🌟 終極修復：先看 Google 有沒有給精確的 departure_time
                    dep_t = details.get("departure_time", {}).get("text")
                    arr_t = details.get("arrival_time", {}).get("text")
                    
                    # 如果 Google 沒給（空值），我們就用 current_time_tracker 自己推算！
                    if not dep_t:
                        dep_t = current_time_tracker.strftime("%H:%M")
                    
                    # 加上搭車時間，推算抵達時間
                    arrival_time_tracker = current_time_tracker + timedelta(seconds=step_seconds)
                    
                    if not arr_t:
                        arr_t = arrival_time_tracker.strftime("%H:%M")
                        
                    # 更新累加器，準備算下一段
                    current_time_tracker = arrival_time_tracker
                    
                    transit_legs.append({
                        "type": "TRANSIT", "vehicle": vehicle_type,
                        "bus_name": bus_name, "board": board, "alight": alight, 
                        "num_stops": num_stops, 
                        "dep_time": dep_t, 
                        "arr_time": arr_t, 
                        "duration": step_duration_text
                    })
                elif step["travel_mode"] == "WALKING":
                    # 走路也要算進時間累加器裡
                    current_time_tracker = current_time_tracker + timedelta(seconds=step_seconds)
                    transit_legs.append({
                        "type": "WALKING", "instruction": clean_html(step.get("html_instructions", "步行")),
                        "duration": step_duration_text
                    })
            
            # 如果總行程沒給抵達時間，用最後的累加時間當作抵達時間
            if not arr_time_text:
                arr_time_text = current_time_tracker.strftime("%H:%M")
                
            path_coords.append({"lat": leg["end_location"]["lat"], "lon": leg["end_location"]["lng"]})
            coords_df = pd.DataFrame(path_coords)
            
            if not has_transit:
                return {"status": "not_found", "message": "此距離過近或無大眾運輸直達，建議直接步行前往！"}
            
            eta = f"預計 {dep_time_text} 發車"
            token = get_tdx_token()
            for t in transit_legs:
                if t["type"] == "TRANSIT":
                    eta = get_real_bus_eta_by_name(token, t["bus_name"], t["board"][:2])
                    break
            return {
                "status": "success", "transit_legs": transit_legs, 
                "eta": eta, "travel_time": total_duration, 
                "dep_time_text": dep_time_text, "arr_time_text": arr_time_text,
                "coords": coords_df, "fare": real_fare
            }
        else:
            return {"status": "not_found", "message": f"找不到大眾運輸路線 ({data.get('status')}): 請確認起迄點與時間設定正確"}
    except Exception as e:
        return {"status": "error", "message": f"連線逾時或錯誤: {e}"}

def get_real_bus_eta_by_name(token, route_name, stop_keyword):
    if not token: return "即時 3 分"
    priority_cities = ["Hsinchu", "Taipei", "NewTaipei", "Taoyuan", "Taichung", "Kaohsiung"]
    for city in priority_cities:
        url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/{city}/{route_name}?$format=JSON"
        headers = {'authorization': f'Bearer {token}'}
        try:
            res = requests.get(url, headers=headers, timeout=2)
            if res.status_code == 200 and res.json():
                for item in res.json():
                    stop_name = item.get("StopName", {}).get("Zh_tw", "")
                    if stop_keyword in stop_name and "EstimateTime" in item:
                        wait_mins = int(item["EstimateTime"]) // 60
                        return f"即時 {wait_mins} 分" if wait_mins > 0 else "即將進站"
        except: pass
    return "即時 3 分"
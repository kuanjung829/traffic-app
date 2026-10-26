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

def get_google_transit_route(start_loc, dest_loc, mode="live", target_datetime=None, time_type="departure"):
    if not GOOGLE_MAPS_API_KEY or GOOGLE_MAPS_API_KEY == '請填寫你的GOOGLE_MAPS_API金鑰':
        return {"status": "error", "message": "尚未設定 Google API 金鑰！"}

    url = "https://maps.googleapis.com/maps/api/directions/json"
    
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
    
    if mode == "specific" and target_datetime:
        if time_type == "arrival":
            params["arrival_time"] = timestamp
        else:
            params["departure_time"] = timestamp
    else:
        params["departure_time"] = timestamp
            
    try:
        res = requests.get(url, params=params, timeout=8)
        data = res.json()
        
        if data.get("status") == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            real_fare = route.get("fare", {}).get("value", 15)
            total_duration_text = leg["duration"]["text"]
            total_duration_sec = leg["duration"].get("value", 0)
            
            dep_time_text = leg.get("departure_time", {}).get("text")
            arr_time_text = leg.get("arrival_time", {}).get("text")
            
            # 🌟 核心修復：正確處理正向與反向推算的時間基準點
            if time_type == "arrival":
                # 反向推算：已知抵達時間，回推發車時間
                if not arr_time_text:
                    arr_time_text = base_datetime.strftime("%H:%M")
                if not dep_time_text:
                    # 用 抵達時間 減去 總車程，精準逆推發車時間
                    calculated_dep = base_datetime - timedelta(seconds=total_duration_sec)
                    dep_time_text = calculated_dep.strftime("%H:%M")
                # 設定追蹤器起點為「減去車程後的真實出發時間」
                current_time_tracker = base_datetime - timedelta(seconds=total_duration_sec)
            else:
                # 正向推算：已知出發時間，推算抵達時間
                if not dep_time_text:
                    dep_time_text = base_datetime.strftime("%H:%M")
                if not arr_time_text:
                    calculated_arr = base_datetime + timedelta(seconds=total_duration_sec)
                    arr_time_text = calculated_arr.strftime("%H:%M")
                # 設定追蹤器起點為「出發時間」
                current_time_tracker = base_datetime

            # 校準時間追蹤器
            try:
                dt_obj = datetime.datetime.strptime(dep_time_text, "%H:%M")
                current_time_tracker = current_time_tracker.replace(hour=dt_obj.hour, minute=dt_obj.minute)
            except:
                pass

            transit_legs = []
            path_coords = []
            has_transit = False
            
            for step in leg["steps"]:
                path_coords.append({"lat": step["start_location"]["lat"], "lon": step["start_location"]["lng"]})
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
                    
                    dep_t = details.get("departure_time", {}).get("text")
                    arr_t = details.get("arrival_time", {}).get("text")
                    
                    if not dep_t:
                        dep_t = current_time_tracker.strftime("%H:%M")
                    
                    arrival_time_tracker = current_time_tracker + timedelta(seconds=step_seconds)
                    if not arr_t:
                        arr_t = arrival_time_tracker.strftime("%H:%M")
                        
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
                    current_time_tracker = current_time_tracker + timedelta(seconds=step_seconds)
                    transit_legs.append({
                        "type": "WALKING", "instruction": clean_html(step.get("html_instructions", "步行")),
                        "duration": step_duration_text
                    })
            
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
                "eta": eta, "travel_time": total_duration_text, 
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
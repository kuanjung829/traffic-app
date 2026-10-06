import time
import requests
import pandas as pd
import streamlit as st

# ==========================================
# 核心模組一：API 金鑰設定 (TDX & Google Maps)
# ==========================================
# TDX API 金鑰
TDX_CLIENT_ID = 'kuanjung829-5b32ef80-7be0-4ebe'
TDX_CLIENT_SECRET = '98aa31ee-f7d1-408c-af85-8d1887791ad9'

# 👇 請在這裡貼上你剛剛申請到的 Google Maps API 金鑰 👇
GOOGLE_MAPS_API_KEY = '請貼上你的GOOGLE_MAPS_API金鑰' 
# 👆 ------------------------------------------- 👆

@st.cache_data(ttl=3000) 
def get_tdx_token():
    """向 TDX 伺服器請求 Access Token"""
    auth_url = "https://tdx.transportdata.tw/auth/realms/TDXConnect/protocol/openid-connect/token"
    data = {'grant_type': 'client_credentials', 'client_id': TDX_CLIENT_ID, 'client_secret': TDX_CLIENT_SECRET}
    try:
        res = requests.post(auth_url, data=data)
        if res.status_code == 200:
            return res.json().get('access_token')
    except Exception as e:
        pass
    return None

def get_real_bus_eta(token, route_name, stop_keyword):
    """取得 TDX 指定路線與站牌的即時動態"""
    if not token: return "預估 5"
    url = f"https://tdx.transportdata.tw/api/basic/v2/Bus/EstimatedTimeOfArrival/City/Hsinchu/{route_name}?$format=JSON"
    headers = {'authorization': f'Bearer {token}'}
    try:
        res = requests.get(url, headers=headers, timeout=5)
        if res.status_code == 200:
            for item in res.json():
                stop_name = item.get("StopName", {}).get("Zh_tw", "")
                if stop_keyword in stop_name and "EstimateTime" in item:
                    wait_mins = int(item["EstimateTime"]) // 60
                    return f"即時 {wait_mins}" if wait_mins > 0 else "即將進站"
            return "未發車"
    except:
        pass
    return "預估 8"

# ==========================================
# 核心模組二：Google Maps 路線規劃大腦
# ==========================================
def get_google_transit_route(start_loc, dest_loc):
    """直接呼叫 Google Maps API 計算大眾運輸路線"""
    
    # 防呆機制：確保使用者有填寫金鑰
    if GOOGLE_MAPS_API_KEY == '請貼上你的GOOGLE_MAPS_API金鑰' or not GOOGLE_MAPS_API_KEY:
        return {"status": "error", "message": "請先在程式碼中填寫 Google Maps API 金鑰！"}

    # 準備呼叫 Google Directions API 的網址與參數
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": f"新竹市 {start_loc}", # 加上新竹市讓搜尋更精準
        "destination": f"新竹市 {dest_loc}",
        "mode": "transit",               # 指定為大眾運輸
        "language": "zh-TW",
        "key": GOOGLE_MAPS_API_KEY
    }
    
    try:
        # 直接使用 requests 發送請求給 Google！
        response = requests.get(url, params=params)
        data = response.json()
        
        # 檢查 Google 有沒有找到路線
        if data.get("status") == "OK":
            route = data["routes"][0]["legs"][0]
            
            # 準備萃取路線資料
            start_coord = route["start_location"]
            end_coord = route["end_location"]
            total_duration = route["duration"]["text"]
            
            # 尋找大眾運輸的步驟 (過濾掉純走路的步驟)
            transit_step = None
            for step in route["steps"]:
                if step["travel_mode"] == "TRANSIT":
                    transit_step = step["transit_details"]
                    break
                    
            if transit_step:
                bus_name = transit_step["line"].get("short_name", transit_step["line"].get("name"))
                board_stop = transit_step["departure_stop"]["name"]
                alight_stop = transit_step["arrival_stop"]["name"]
                
                # 拿 Google 算出來的公車，去問 TDX 即時時間！(Hybrid 結合)
                token = get_tdx_token()
                # 這裡簡單取站牌前兩個字去 TDX 模糊比對
                eta = get_real_bus_eta(token, bus_name, board_stop[:2]) 
                
                # 組合介面需要的資料格式
                coords_df = pd.DataFrame([
                    {"lat": start_coord["lat"], "lon": start_coord["lng"], "name": f"起點：{start_loc}"},
                    {"lat": end_coord["lat"], "lon": end_coord["lng"], "name": f"終點：{dest_loc}"}
                ])
                
                route_options = [{
                    "option_id": 1,
                    "bus_route_name": bus_name,
                    "boarding_stop": board_stop,
                    "alighting_stop": alight_stop,
                    "estimated_wait": eta,
                    "travel_time_mins": total_duration,
                    "fare": 15 # 預設市區公車票價
                }]
                
                return {"status": "success", "route_options": route_options, "coords": coords_df}
            else:
                return {"status": "not_found", "message": f"Google Maps 建議從「{start_loc}」到「{dest_loc}」直接走路即可，無需搭乘大眾運輸！"}
        else:
            return {"status": "not_found", "message": f"Google Maps 找不到從「{start_loc}」到「{dest_loc}」的大眾運輸路線。"}
            
    except Exception as e:
        return {"status": "error", "message": f"呼叫 Google API 時發生錯誤: {e}"}

# ==========================================
# 前端介面設計 (Streamlit UI)
# ==========================================
st.set_page_config(page_title="AI 智慧公車導航 (Google Maps版)", page_icon="🚌", layout="wide")

if "step" not in st.session_state: st.session_state.step = "search"
if "selected_route" not in st.session_state: st.session_state.selected_route = None
if "wallet_balance" not in st.session_state: st.session_state.wallet_balance = 500
if "ride_history" not in st.session_state: st.session_state.ride_history = []

with st.sidebar:
    st.title("👤 會員專區")
    st.markdown("### 何冠融")
    st.caption("🏫 磐石高中 | 學生帳戶")
    st.divider()
    
    st.metric("💳 虛擬錢包餘額", f"NT$ {st.session_state.wallet_balance}")
    st.markdown("✅ **綁定支付**：中華電信帳單代收")
    st.markdown("✅ **身分優惠**：學生票已啟用")
    
    st.divider()
    st.markdown("### 📜 歷史乘車紀錄")
    if not st.session_state.ride_history:
        st.info("尚無搭乘紀錄")
    else:
        for ride in reversed(st.session_state.ride_history):
            st.markdown(f"- **{ride['route']}**: {ride['start']}➔{ride['end']} <span style='color:red;'>(-${ride['fare']})</span>", unsafe_allow_html=True)
            st.caption(f"🕒 {ride['time']}")

st.title("🌍 AI 智慧公車無感支付與動態導航 (串接 Google 大腦)")
st.caption("🟢 Hybrid 架構：Google Maps 提供全域路徑規劃 + TDX 提供即時車況")

col1, col2 = st.columns(2)
with col1:
    start_input = st.text_input("📍 目前位置 / 出發地", placeholder="例如：新竹火車站")
with col2:
    dest_input = st.text_input("🏁 您想去哪裡 (目的地)？", placeholder="例如：六福村")

if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
    if start_input and dest_input:
        st.session_state.start_loc = start_input
        st.session_state.dest_loc = dest_input
        with st.spinner("🚀 正在呼叫 Google Maps 超級大腦規劃路線..."):
            st.session_state.route_result = get_google_transit_route(start_input, dest_input)
        st.session_state.step = "search_done"
    else:
        st.error("⚠️ 請確保出發地與目的地都已填寫！")

if "dest_loc" in st.session_state and st.session_state.step in ["search_done", "search"]:
    route_result = st.session_state.route_result
    
    if route_result["status"] == "success":
        st.success(f"✅ Google Maps 成功為您規劃：**{st.session_state.start_loc}** ➔ **{st.session_state.dest_loc}**")
        
        map_col, route_col = st.columns([1.2, 1])
        with map_col:
            st.subheader("🗺️ 路線起迄點地圖")
            st.map(route_result["coords"], zoom=12, use_container_width=True)
            
        with route_col:
            st.subheader("💡 推薦搭乘路線 (結合 TDX 動態)")
            for opt in route_result["route_options"]:
                with st.container(border=True):
                    st.markdown(f"### 🚍 {opt['bus_route_name']}")
                    wait_time_display = f"{opt['estimated_wait']} 分鐘" if "即時" in opt['estimated_wait'] else opt['estimated_wait']
                    st.markdown(f"**預估等候**: `{wait_time_display}` | **車程**: `{opt['travel_time_mins']}`")
                    st.text(f"📍 {opt['boarding_stop']} \n➔ {opt['alighting_stop']}")
                    
                    if st.button(f"確認搭乘 ({opt['bus_route_name']})", key=f"btn_{opt['option_id']}", use_container_width=True):
                        st.session_state.selected_route = opt
                        st.session_state.step = "payment_simulation"
                        st.rerun()
    elif route_result["status"] == "error":
        st.error(route_result["message"])
    else:
        st.warning(route_result["message"])

if st.session_state.step == "payment_simulation":
    opt = st.session_state.selected_route
    st.markdown("---")
    st.subheader("🔄 車載 Edge AI 感應與無感支付進行中...")
    
    with st.status("正在與車載系統建立連線...", expanded=True) as status:
        st.write("📡 階段 1/3：已向後端寫入待扣款狀態 (`Ready to Board`)")
        time.sleep(0.8)
        st.write(f"🚌 階段 2/3：車載 AI 鏡頭與手機藍牙訊號比對中 (班次: {opt['bus_route_name']})...")
        time.sleep(1.0)
        st.write("✨ 階段 3/3：身分特徵匹配成功！正在自動觸發電子支付...")
        time.sleep(0.8)
        
        if st.session_state.wallet_balance >= opt['fare']:
            st.session_state.wallet_balance -= opt['fare']
            current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            st.session_state.ride_history.append({
                "route": opt['bus_route_name'],
                "start": opt['boarding_stop'],
                "end": opt['alighting_stop'],
                "fare": opt['fare'],
                "time": current_time
            })
            status.update(label="🎉 無感支付與乘車綁定成功！", state="complete", expanded=False)
            st.balloons()
            payment_success = True
        else:
            status.update(label="❌ 餘額不足，扣款失敗！", state="error", expanded=False)
            payment_success = False

    if payment_success:
        with st.container(border=True):
            st.markdown("### 💳 數位乘車憑證與交易收據")
            st.markdown(f"- **搭乘班次**：`{opt['bus_route_name']}`")
            st.markdown(f"- **乘車區間**：{opt['boarding_stop']} ➔ {opt['alighting_stop']}")
            st.markdown(f"- **扣款金額**：**NT$ {opt['fare']} 元**")
            st.markdown("- **支付狀態**：<span style='color:green;'>**已自動扣款 (無感支付完成)**</span>", unsafe_allow_html=True)
            st.markdown(f"- **帳戶剩餘餘額**：NT$ {st.session_state.wallet_balance} 元")
        
        st.info("💡 提示：您已可直接上車找位子坐，無需刷任何卡片或條碼！")
    else:
        st.error("請儲值您的虛擬錢包後再試一次。")
        
    if st.button("🔄 完成這趟旅程，返回首頁"):
        st.session_state.step = "search"
        st.session_state.selected_route = None
        st.rerun()
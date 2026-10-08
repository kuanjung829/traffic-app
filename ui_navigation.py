# ui_navigation.py
import streamlit as st
import time
from database import save_db
from api_services import get_google_transit_route, get_tdx_token, get_location_coordinates, get_nearby_stops, get_stop_eta

def render_navigation_tab(db, user_email):
    user_data = db["users"][user_email]
    
    has_face = bool(user_data.get("face_verified", False))
    
    if not has_face:
        st.info("💡 **AI 無感支付解鎖提醒**：目前您可以自由查詢公車路線與地圖預覽。若要啟用「一鍵自動扣款」功能，請先至左側完成 **AI 人臉識別驗證**！")
    
    if "route_result" not in st.session_state:
        st.session_state.route_result = None
    if "success_msg" not in st.session_state:
        st.session_state.success_msg = ""
    if "is_booked" not in st.session_state:
        st.session_state.is_booked = False

    if st.session_state.route_result is None:
        col_s, col_d = st.columns(2)
        start_input = col_s.text_input("📍 出發地", placeholder="例如：清華大學", key="nav_start")
        dest_input = col_d.text_input("🏁 目的地", placeholder="例如：新竹火車站", key="nav_dest")
        
        if st.button("🚀 開始路線查詢", type="primary", use_container_width=True, key="nav_btn"):
            if start_input and dest_input:
                st.session_state.success_msg = ""
                st.session_state.is_booked = False
                with st.spinner("🚀 正在為您規劃最快路徑 (包含公車與轉乘)..."):
                    st.session_state.route_result = get_google_transit_route(start_input, dest_input)
                    st.session_state.start_loc = start_input
                    st.session_state.dest_loc = dest_input
                    st.rerun()
    else:
        result = st.session_state.route_result
        start_input = st.session_state.get("start_loc", "")
        dest_input = st.session_state.get("dest_loc", "")
        
        if st.button("🔄 返回重新搜尋其他路線", key="nav_back_btn"):
            st.session_state.route_result = None
            st.session_state.success_msg = ""
            st.session_state.is_booked = False
            st.rerun()
            
        if result["status"] == "success":
            st.success("✅ 路線規劃成功！")
            m_col, r_col = st.columns([1.2, 1])
            
            with m_col:
                st.subheader("🗺️ 導航路徑圖")
                st.map(result["coords"], zoom=13, use_container_width=True)
            
            with r_col:
                st.subheader("💡 詳細搭乘步驟")
                st.markdown(f"**總車程預估**: `{result['travel_time']}` | **即時等候**: `{result['eta']}`")
                
                main_bus = "公車"
                with st.container(border=True):
                    for i, leg in enumerate(result["transit_legs"]):
                        if leg["type"] == "WALKING":
                            st.markdown(f"🚶‍♂️ **步行** (`{leg['duration']}`)：{leg['instruction']}")
                            
                        elif leg["type"] == "TRANSIT":
                            main_bus = leg['bus_name']
                            st.markdown(f"### 🚍 搭乘 【{leg['bus_name']}】")
                            st.caption(f"預計發車: 🕒 **{leg['dep_time']}** | 乘車時間: {leg['duration']} ({leg['num_stops']} 站)")
                            st.markdown(f"📍 **上車**：`{leg['board']}`")
                            st.markdown(f"🏁 **下車**：`{leg['alight']}`")
                            
                        if i < len(result["transit_legs"])-1:
                            st.markdown("👇")
                            
                    fare = result['fare'] if not user_data["is_student"] else int(result['fare'] * 0.8)
                    st.markdown(f"--- \n💵 **真實票價：NT$ {fare}** (已套用學生 8 折)")
                    
                    if not st.session_state.is_booked:
                        if has_face:
                            if st.button("確認搭乘 (AI 影像識別無感扣款)", use_container_width=True, type="primary", key="book_btn"):
                                if user_data["balance"] >= fare:
                                    user_data["balance"] -= fare
                                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                    user_data["history"].append({
                                        "route": main_bus,
                                        "start": start_input,
                                        "end": dest_input,
                                        "fare": fare,
                                        "time": current_time,
                                        "status": "valid"
                                    })
                                    save_db(db)
                                    st.session_state.is_booked = True
                                    st.session_state.success_msg = f"🎉 AI 感知支付成功！已透過人臉識別從錢包扣除 NT$ {fare}。"
                                    st.rerun()
                                else:
                                    st.error("❌ 錢包餘額不足！請至左側「儲值中心」儲值後再試。")
                        else:
                            st.warning("🔒 無感支付已鎖定：請先至左側完成 **AI 人臉識別驗證** 才能解鎖扣款功能。")
                            st.button("🔒 尚未解鎖 (缺少: AI 人臉識別)", use_container_width=True, disabled=True, key="locked_btn")
                    else:
                        st.success(st.session_state.success_msg)
        else:
            st.warning(result["message"])

def render_nearby_tab():
    st.subheader("📍 附近站牌與路線動態")
    location_input = st.text_input("輸入您目前的地點或地址", placeholder="例如：台北車站 或 台北市信義區市府路1號")
    
    if st.button("🔍 搜尋附近站牌", type="primary", use_container_width=True):
        if not location_input:
            st.warning("請先輸入地點！")
            return
            
        with st.spinner("🌍 正在尋找附近的站牌..."):
            coords = get_location_coordinates(location_input)
            # --- 加入這行除錯碼 ---
            st.write(f"除錯訊息：抓到的經緯度是 {coords}")
            # --------------------
            if not coords:
                st.error("❌ 找不到該地點，請嘗試輸入更完整的地址或地標。")
                return
                
            lat, lon = coords
            token = get_tdx_token()
            nearby_stops = get_nearby_stops(token, lat, lon)
            
            if not nearby_stops:
                st.info("😅 在 500 公尺內沒有找到公車站牌。")
                return
                
            st.success(f"找到了！ {location_input} 附近有 {len(nearby_stops)} 個站牌：")
            
            # 🌟 關鍵修正：解析 StopName (站牌) 欄位
            unique_stops = {}
            for stop in nearby_stops:
                name = stop.get("StopName", {}).get("Zh_tw")
                if not name: continue
                if name not in unique_stops:
                    unique_stops[name] = {
                        "uid": stop.get("StopUID"),
                        "address": f"站牌編號: {stop.get('StopID', '無')}"
                    }
                    
            for name, info in unique_stops.items():
                with st.expander(f"🚏 {name}"):
                    st.caption(f"位置：{info['address']}")
                    
                    if st.button(f"查詢 {name} 路線動態", key=f"btn_{info['uid']}"):
                        with st.spinner("獲取動態中..."):
                            etas = get_stop_eta(token, info['uid'])
                            if etas:
                                for eta_info in etas:
                                    st.write(f"🚍 **{eta_info['route']}**：`{eta_info['eta']}`")
                            else:
                                st.write("目前沒有車輛資訊。")
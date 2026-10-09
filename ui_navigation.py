# ui_navigation.py
import streamlit as st
import time
import datetime
from database import save_db
from api_services import get_google_transit_route

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
        st.subheader("📍 智能路線規劃")
        
        col_s, col_d = st.columns(2)
        start_input = col_s.text_input("📍 出發地", placeholder="例如：清華大學")
        dest_input = col_d.text_input("🏁 目的地", placeholder="例如：新竹火車站")
        
        st.markdown("---")
        
        query_type = st.radio("選擇查詢模式", ["⚡ 即時查詢 (馬上出發)", "🕒 特定查詢 (同時設定出發與到達時間)"], horizontal=True)
        
        target_datetime = None
        target_arrival_datetime = None
        
        if query_type == "🕒 特定查詢 (同時設定出發與到達時間)":
            st.markdown("##### ⚙️ 請設定您的行程時間範圍（系統將為您尋找最貼切的班次）")
            
            col_date, col_dep, col_arr = st.columns([1.2, 1, 1])
            selected_date = col_date.date_input("選擇日期", datetime.date.today())
            
            dep_time_val = col_dep.time_input("🕒 預計出發時間", datetime.datetime.now().time())
            
            default_arr = (datetime.datetime.combine(datetime.date.today(), dep_time_val) + datetime.timedelta(hours=1)).time()
            arr_time_val = col_arr.time_input("🏁 希望抵達時間", default_arr)
            
            target_datetime = datetime.datetime.combine(selected_date, dep_time_val)
            target_arrival_datetime = datetime.datetime.combine(selected_date, arr_time_val)
            
        st.markdown("")
        
        if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
            if start_input and dest_input:
                st.session_state.success_msg = ""
                st.session_state.is_booked = False
                
                mode_str = "live" if "即時" in query_type else "specific"
                
                with st.spinner("🚀 正在為您計算最佳時間段與轉乘方案..."):
                    st.session_state.route_result = get_google_transit_route(
                        start_input, dest_input, mode=mode_str, time_mode="出發時間", target_datetime=target_datetime
                    )
                    st.session_state.start_loc = start_input
                    st.session_state.dest_loc = dest_input
                    st.session_state.target_arrival = target_arrival_datetime 
                    st.rerun()
            else:
                st.warning("請完整填寫出發地與目的地！")
    else:
        result = st.session_state.route_result
        start_input = st.session_state.get("start_loc", "")
        dest_input = st.session_state.get("dest_loc", "")
        
        if st.button("🔄 返回重新搜尋"):
            st.session_state.route_result = None
            st.session_state.success_msg = ""
            st.session_state.is_booked = False
            st.rerun()
            
        if result["status"] == "success":
            st.success("✅ 路線規劃成功！已為您配對最貼切時間段的班次。")
            m_col, r_col = st.columns([1.2, 1])
            
            with m_col:
                st.subheader("🗺️ 導航路徑圖")
                st.map(result["coords"], zoom=13, use_container_width=True)
            
            with r_col:
                st.subheader("💡 詳細搭乘步驟與時間")
                # 使用 .get() 確保不會因為空值出錯
                st.markdown(f"🕒 **預計發車**: `{result.get('dep_time_text', '即時出發')}` ➔ 🏁 **預計抵達**: `{result.get('arr_time_text', '依車程計算')}`")
                st.markdown(f"⏱️ **總車程預估**: `{result['travel_time']}`")
                
                main_bus = "公車"
                with st.container(border=True):
                    for i, leg in enumerate(result["transit_legs"]):
                        if leg["type"] == "WALKING":
                            st.markdown(f"🚶‍♂️ **步行** (`{leg['duration']}`)：{leg['instruction']}")
                            
                        elif leg["type"] == "TRANSIT":
                            main_bus = leg['bus_name']
                            st.markdown(f"### 🚍 搭乘 【{leg['bus_name']}】")
                            # 🌟 關鍵改動：並列顯示單一公車的發車與抵達時間
                            st.caption(f"🕒 發車: **{leg.get('dep_time', '隨時發車')}** ➔ 🏁 抵達: **{leg.get('arr_time', '依車程抵達')}** | 乘車時間: {leg['duration']} ({leg['num_stops']} 站)")
                            st.markdown(f"📍 **上車**：`{leg['board']}`")
                            st.markdown(f"🏁 **下車**：`{leg['alight']}`")
                            
                        if i < len(result["transit_legs"])-1:
                            st.markdown("👇")
                            
                    fare = result['fare'] if not user_data["is_student"] else int(result['fare'] * 0.8)
                    st.markdown(f"--- \n💵 **真實票價：NT$ {fare}** (已套用學生 8 折)")
                    
                    if not st.session_state.is_booked:
                        if has_face:
                            if st.button("確認搭乘 (AI 影像識別無感扣款)", use_container_width=True, type="primary"):
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
                            st.button("🔒 尚未解鎖 (缺少: AI 人臉識別)", use_container_width=True, disabled=True)
                    else:
                        st.success(st.session_state.success_msg)
        else:
            st.warning(result["message"])
# ui_navigation.py
import streamlit as st
import time
import datetime
from database import save_db
from api_services import get_google_transit_route_with_time

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
        st.subheader("📍 智能路線與時間段規劃")
        
        col_s, col_d = st.columns(2)
        start_input = col_s.text_input("📍 出發地", placeholder="例如：清華大學")
        dest_input = col_d.text_input("🏁 目的地", placeholder="例如：新竹火車站")
        
        st.markdown("---")
        st.markdown("### 🕒 選擇時間段設定")
        
        col_mode, col_date, col_time = st.columns([1, 1.2, 1.2])
        time_mode = col_mode.selectbox("時間模式", ["出發時間", "預計抵達時間"])
        
        # 預設為今天
        default_date = datetime.date.today()
        selected_date = col_date.date_input("選擇日期", default_date)
        
        # 預設為現在時間
        default_time = datetime.datetime.now().time()
        selected_time = col_time.time_input("選擇時間點", default_time)
        
        # 合併日期與時間成為 datetime 物件
        target_datetime = datetime.datetime.combine(selected_date, selected_time)
        
        st.markdown("")
        if st.button("🚀 尋找最佳轉乘路線", type="primary", use_container_width=True):
            if start_input and dest_input:
                st.session_state.success_msg = ""
                st.session_state.is_booked = False
                with st.spinner("🚀 正在為您計算最佳時間段與轉乘方案..."):
                    st.session_state.route_result = get_google_transit_route_with_time(
                        start_input, dest_input, time_mode, target_datetime
                    )
                    st.session_state.start_loc = start_input
                    st.session_state.dest_loc = dest_input
                    st.rerun()
            else:
                st.warning("請完整填寫出發地與目的地！")
    else:
        result = st.session_state.route_result
        start_input = st.session_state.get("start_loc", "")
        dest_input = st.session_state.get("dest_loc", "")
        
        if st.button("🔄 返回重新設定起迄點與時間段"):
            st.session_state.route_result = None
            st.session_state.success_msg = ""
            st.session_state.is_booked = False
            st.rerun()
            
        if result["status"] == "success":
            st.success("✅ 已為您配對最佳時間段路線！")
            m_col, r_col = st.columns([1.2, 1])
            
            with m_col:
                st.subheader("🗺️ 導航路徑圖")
                st.map(result["coords"], zoom=13, use_container_width=True)
            
            with r_col:
                st.subheader("💡 詳細搭乘步驟與時間段")
                st.markdown(f"🕒 **預計發車**: `{result['dep_time_text']}` ➔ 🏁 **預計抵達**: `{result['arr_time_text']}`")
                st.markdown(f"⏱️ **總車程預估**: `{result['travel_time']}`")
                
                main_bus = "公車"
                with st.container(border=True):
                    for i, leg in enumerate(result["transit_legs"]):
                        if leg["type"] == "WALKING":
                            st.markdown(f"🚶‍♂️ **步行** (`{leg['duration']}`)：{leg['instruction']}")
                            
                        elif leg["type"] == "TRANSIT":
                            main_bus = leg['bus_name']
                            st.markdown(f"### 🚍 搭乘 【{leg['bus_name']}】")
                            st.caption(f"發車時間: 🕒 **{leg['dep_time']}** | 乘車時間: {leg['duration']} ({leg['num_stops']} 站)")
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
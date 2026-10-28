import streamlit as st
import time
import datetime
from database import save_db
import api_services 

def render_navigation(db, user_email):
    user_data = db["users"][user_email]

    if "frozen_balance" not in user_data:
        user_data["frozen_balance"] = 0
    if "history" not in user_data:
        user_data["history"] = []

    pending_orders = [o for o in user_data["history"] if o.get("status") == "pending"]

    if pending_orders:
        st.subheader("📍 智能路線與預約搭乘")
        st.warning(f"⚠️ 您目前有 {len(pending_orders)} 段尚未搭乘的轉乘訂單！請依序上車刷臉，或取消剩餘預約。")
        
        next_order = pending_orders[0]
        st.write(f"**即將搭乘**: {next_order['route']}")
        st.write(f"**本段凍結票價**: NT$ {next_order['fare']}")
        
        total_pending_fare = sum(o["fare"] for o in pending_orders)

        if st.button("❌ 取消剩餘所有預約 (退回未扣款項)", use_container_width=True):
            for o in user_data["history"]:
                if o.get("status") == "pending":
                    user_data["balance"] += o["fare"]
                    user_data["frozen_balance"] -= o["fare"]
                    o["status"] = "canceled"
            save_db(db)
            st.success(f"✅ 已成功取消後續行程，共解凍退回 NT$ {total_pending_fare}！")
            time.sleep(1.5)
            st.rerun()
    else:
        st.subheader("📍 智能路線與預約搭乘")

        # 🌟 UI 優化：將出發地與目的地使用 Columns 並排顯示
        loc_col1, loc_col2 = st.columns(2)
        with loc_col1:
            start_loc = st.text_input("📍 出發地", placeholder="例如：磐石中學")
        with loc_col2:
            end_loc = st.text_input("📍 目的地", placeholder="例如：新竹火車站")
        
        # 將單選按鈕改成橫向排列，節省空間
        mode = st.radio("選擇查詢模式", [
            "⚡ 即時查詢 (馬上出發)", 
            "🕒 特定查詢 (同時設定出發與到達時間)"
        ], horizontal=True)

        selected_date = None
        selected_start_time = None
        selected_end_time = None

        if mode == "🕒 特定查詢 (同時設定出發與到達時間)":
            # 🌟 UI 優化：將時間設定包裝成一個帶邊框的控制面板卡片
            with st.container(border=True):
                st.markdown("⚙️ **行程時間範圍設定**")
                selected_date = st.date_input("📅 選擇日期")
                
                # 將出發與抵達時間並排
                time_col1, time_col2 = st.columns(2)
                with time_col1:
                    selected_start_time = st.time_input("🕒 預計出發時間")
                with time_col2:
                    selected_end_time = st.time_input("🏁 希望抵達時間")

        if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
            if not start_loc or not end_loc:
                st.error("請輸入出發地與目的地！")
            else:
                with st.spinner("📡 正在透過 TDX 與 Google Maps API 計算最佳路線..."):
                    query_start = f"台灣 {start_loc}"
                    query_end = f"台灣 {end_loc}"

                    if mode == "🕒 特定查詢 (同時設定出發與到達時間)":
                        target_dt = datetime.datetime.combine(selected_date, selected_end_time)
                        route_data = api_services.get_google_transit_route(query_start, query_end, mode="specific", target_datetime=target_dt, time_type="arrival")
                        
                        st.session_state.search_title = f"{start_loc} ➔ {end_loc} (需在 {selected_date} {selected_end_time.strftime('%H:%M')} 前抵達)"
                        st.session_state.user_start_time = selected_start_time 
                        st.session_state.user_end_time = selected_end_time 
                    else:
                        route_data = api_services.get_google_transit_route(query_start, query_end, mode="live")
                        st.session_state.search_title = f"{start_loc} ➔ {end_loc} (即時出發)"
                    
                    st.session_state.route_data = route_data
                    st.session_state.dyn_start = start_loc
                    st.session_state.dyn_end = end_loc

        if "route_data" in st.session_state:
            data = st.session_state.route_data
            
            st.markdown("---")
            st.write(f"### 查詢結果：{st.session_state.search_title}")

            if data.get("status") != "success":
                st.error(data.get("message", "路線查詢失敗，請重試。"))
            else:
                if "需在" in st.session_state.search_title:
                    if "user_start_time" in st.session_state and "user_end_time" in st.session_state:
                        api_dep_time_str = data.get('dep_time_text', '')
                        api_arr_time_str = data.get('arr_time_text', '')
                        user_start_time = st.session_state.user_start_time
                        user_end_time = st.session_state.user_end_time
                        
                        try:
                            api_dep_time = datetime.datetime.strptime(api_dep_time_str, "%H:%M").time()
                            api_arr_time = datetime.datetime.strptime(api_arr_time_str, "%H:%M").time()
                            
                            if api_arr_time > user_end_time:
                                st.error(f"🔴 **無法準時抵達**：目前時間已趕不上能在 {user_end_time.strftime('%H:%M')} 前抵達的車次！系統已自動為您尋找最快的下一班車（將於 {api_arr_time_str} 抵達）。")
                            elif api_dep_time < user_start_time:
                                st.warning(f"⚠️ **時間衝突提醒**：為了在 {user_end_time.strftime('%H:%M')} 前抵達，系統反推最晚必須在 **{api_dep_time_str}** 出發，這比您設定的預計出發時間 ({user_start_time.strftime('%H:%M')}) 還早！建議提早出門。")
                            else:
                                st.success(f"✅ **行程銜接順利**：您可以在 {user_start_time.strftime('%H:%M')} 之後從容出發，搭上 **{api_dep_time_str}** 的班次，就能在 {api_arr_time_str} 準時抵達！")
                        except:
                            st.info("💡 **系統反向推算完成：建議您依據以下時間出發！**")
                else:
                    st.write("💡 **詳細搭乘步驟與時間**")
                    
                st.write(f"🕒 預計發車 : {data['dep_time_text']} 🏁 預計抵達 : {data['arr_time_text']}")
                st.write(f"⏱ 總車程預估 : {data['travel_time']}")

                for leg in data["transit_legs"]:
                    if leg["type"] == "WALKING":
                        st.info(f"🚶 **步行 ( {leg['duration']} )** : {leg['instruction']}")
                    elif leg["type"] == "TRANSIT":
                        with st.container(border=True):
                            st.markdown(f"🚌 **搭乘 【{leg['bus_name']}】**")
                            bus_eta = data.get("eta", "正常營運")
                            st.caption(f"營運狀態: 🟢 {bus_eta} | 乘車時間: {leg['duration']} ({leg['num_stops']}站)")
                            st.write(f"📍 **上車**: {leg['board']} ({leg['dep_time']})")
                            st.write(f"🏁 **下車**: {leg['alight']} ({leg['arr_time']})")
                
                st.write("") 

                if "coords" in data and not data["coords"].empty:
                    st.map(data["coords"])
                    st.write("")

                base_fare = data.get("fare", 15) 
                if user_data.get("is_student"):
                    actual_fare = int(base_fare * 0.8)
                    btn_text = f"💵 確認預約並凍結票價：NT$ {actual_fare} (已套用學生 8 折)"
                else:
                    actual_fare = base_fare
                    btn_text = f"💵 確認預約並凍結票價：NT$ {actual_fare}"

                if not user_data.get("face_verified"):
                    st.error("❌ 系統攔截：您尚未完成人臉識別註冊！請先至左側邊欄完成「拍照建模」，才能進行預約。")
                    st.button(btn_text, use_container_width=True, type="primary", disabled=True)
                else:
                    if st.button(btn_text, use_container_width=True, type="primary"):
                        if user_data["balance"] >= actual_fare:
                            user_data["balance"] -= actual_fare
                            user_data["frozen_balance"] += actual_fare

                            transit_legs = [leg for leg in data["transit_legs"] if leg["type"] == "TRANSIT"]
                            num_legs = len(transit_legs)

                            if num_legs > 0:
                                fare_per_leg = actual_fare // num_legs
                                remainder = actual_fare % num_legs
                                
                                for i, leg in enumerate(transit_legs):
                                    leg_fare = fare_per_leg + (remainder if i == 0 else 0)
                                    new_order = {
                                        "route": f"【{leg['bus_name']}】 {leg['board']} ➔ {leg['alight']}",
                                        "fare": leg_fare,
                                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "status": "pending"
                                    }
                                    user_data["history"].append(new_order)
                            else:
                                new_order = {
                                    "route": st.session_state.search_title,
                                    "fare": actual_fare,
                                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "status": "pending"
                                }
                                user_data["history"].append(new_order)

                            save_db(db)

                            st.session_state.pop("route_data", None)
                            st.session_state.pop("search_title", None)
                            st.session_state.pop("dyn_start", None)
                            st.session_state.pop("dyn_end", None)
                            
                            st.success("🎉 分段預約成功！各段車資已凍結，請依序上車刷臉扣款。")
                            time.sleep(1.5)
                            st.rerun()
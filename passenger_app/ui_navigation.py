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

    # 找尋所有尚未搭乘的訂單
    pending_orders = [o for o in user_data["history"] if o.get("status") == "pending"]

    if pending_orders:
        st.subheader("📍 智能路線與預約搭乘")
        st.warning(f"⚠️ 您目前有 {len(pending_orders)} 段尚未搭乘的轉乘訂單！請依序上車刷臉，或取消剩餘預約。")
        
        # 顯示下一趟要搭的車 (取陣列第一筆)
        next_order = pending_orders[0]
        st.write(f"**即將搭乘**: {next_order['route']}")
        st.write(f"**本段凍結票價**: NT$ {next_order['fare']}")
        
        # 計算所有未搭乘的總凍結金額
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

        start_loc = st.text_input("📍 出發地", placeholder="例如：清華大學")
        end_loc = st.text_input("📍 目的地", placeholder="例如：新竹火車站")
        
        mode = st.radio("選擇查詢模式", ["⚡ 即時查詢 (馬上出發)", "🕒 預約查詢 (同時設定出發與到達時間)"])

        selected_date = None
        selected_time = None
        if mode == "🕒 預約查詢 (同時設定出發與到達時間)":
            col1, col2 = st.columns(2)
            with col1:
                selected_date = st.date_input("選擇出發日期")
            with col2:
                selected_time = st.time_input("選擇出發時間")

        if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
            if not start_loc or not end_loc:
                st.error("請輸入出發地與目的地！")
            else:
                with st.spinner("📡 正在透過 TDX 與 Google Maps API 計算最佳路線..."):
                    query_start = f"台灣 {start_loc}"
                    query_end = f"台灣 {end_loc}"

                    if mode == "🕒 預約查詢 (同時設定出發與到達時間)":
                        target_dt = datetime.datetime.combine(selected_date, selected_time)
                        route_data = api_services.get_google_transit_route(query_start, query_end, mode="specific", target_datetime=target_dt)
                        st.session_state.search_title = f"{start_loc} ➔ {end_loc} ({selected_date} {selected_time} 出發)"
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

                if st.button(btn_text, use_container_width=True, type="primary"):
                    if user_data["balance"] >= actual_fare:
                        user_data["balance"] -= actual_fare
                        user_data["frozen_balance"] += actual_fare

                        # 🌟 核心修改：分段拆解訂單邏輯 (Station by Station)
                        transit_legs = [leg for leg in data["transit_legs"] if leg["type"] == "TRANSIT"]
                        num_legs = len(transit_legs)

                        if num_legs > 0:
                            # 將總票價平均分配給每一段搭乘
                            fare_per_leg = actual_fare // num_legs
                            remainder = actual_fare % num_legs
                            
                            for i, leg in enumerate(transit_legs):
                                # 確保除不盡的餘額加在第一趟，總額吻合
                                leg_fare = fare_per_leg + (remainder if i == 0 else 0)
                                new_order = {
                                    "route": f"【{leg['bus_name']}】 {leg['board']} ➔ {leg['alight']}",
                                    "fare": leg_fare,
                                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                    "status": "pending"
                                }
                                user_data["history"].append(new_order) # 寫入好幾張分段車票
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
                    else:
                        st.error(f"❌ 可用餘額不足！您的餘額為 NT$ {user_data['balance']}，需 NT$ {actual_fare}。請先儲值。")
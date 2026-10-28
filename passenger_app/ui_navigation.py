import streamlit as st
import time
import datetime
import re
from database import save_db
import api_services 
import streamlit.components.v1 as components

# 🌟 智慧時間過濾器：專門對付 Google 傳回的「下午 8:16」這類非標準時間格式
def extract_24h_time(time_text):
    try:
        nums = re.findall(r'\d+', time_text)
        if len(nums) >= 2:
            h = int(nums[0])
            m = int(nums[1])
            # 轉換為 24 小時制
            if "下午" in time_text or "pm" in time_text.lower():
                if h < 12: h += 12
            elif "上午" in time_text or "am" in time_text.lower():
                if h == 12: h = 0
            return f"{h:02d}:{m:02d}:00"
    except:
        pass
    return time.strftime("%H:%M:00")

def render_navigation(db, user_email):
    user_data = db["users"][user_email]

    if "frozen_balance" not in user_data:
        user_data["frozen_balance"] = 0
    if "history" not in user_data:
        user_data["history"] = []

    pending_orders = [o for o in user_data["history"] if o.get("status") == "pending"]

    tab1, tab2 = st.tabs(["🗺️ 路線規劃與搭乘", "📜 我的歷史訂單"])

    # ==========================================
    # 第一頁籤：路線查詢與預約
    # ==========================================
    with tab1:
        if pending_orders:
            st.info("💡 溫馨提醒：您必須完成當前行程或取消預約，才能進行新的路線查詢。")
            
            next_order = pending_orders[0]
            dep_dt_str = next_order.get("dep_datetime")
            dep_dt = None
            is_expired = False
            
            # 1. 嘗試解析資料庫裡的時間
            if dep_dt_str:
                try:
                    dep_dt = datetime.datetime.strptime(dep_dt_str, "%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            # 2. 終極防呆：如果解析失敗（遇到髒資料）或舊訂單，拿「下單時間 + 5分鐘」作為預設發車時間保底
            if not dep_dt:
                try:
                    order_time = datetime.datetime.strptime(next_order.get("time", time.strftime("%Y-%m-%d %H:%M:%S")), "%Y-%m-%d %H:%M:%S")
                    dep_dt = order_time + datetime.timedelta(minutes=5)
                except:
                    dep_dt = datetime.datetime.now() + datetime.timedelta(minutes=5)

            # 3. 正常執行倒數邏輯 (1 分鐘緩衝)
            deadline_dt = dep_dt + datetime.timedelta(minutes=1)
            now = datetime.datetime.now()
            
            if now > deadline_dt:
                is_expired = True
                user_data["frozen_balance"] -= next_order["fare"]
                next_order["status"] = "missed"
                save_db(db)
                
                st.error(f"🚨 **違約扣款通知**\n\n您未於發車與停靠緩衝時間內上車 ({next_order['route']})，系統已自動沒收並扣除違約車資 NT$ {next_order['fare']}。")
                if st.button("🔄 刷新頁面", use_container_width=True):
                    st.rerun()
            else:
                deadline_ts = int(deadline_dt.timestamp() * 1000)
                
                countdown_html = f"""
                <div style="background-color:#fff3cd; border:1px solid #ffeeba; color:#856404; padding:15px; border-radius:10px; text-align:center; font-family:sans-serif; margin-bottom:10px;">
                    <div style="font-size:16px; margin-bottom:5px;">🚌 <b>{next_order['route']}</b></div>
                    <div style="font-size:14px; color:#666;">預計發車：{dep_dt.strftime('%H:%M')} (含 1 分鐘靠站寬限)</div>
                    <h2 style="margin:10px 0 5px 0; color:#dc3545; font-weight:bold;" id="timer">計算中...</h2>
                </div>
                <script>
                    var countDownDate = {deadline_ts};
                    var x = setInterval(function() {{
                        var now = new Date().getTime();
                        var distance = countDownDate - now;
                        if (distance < 0) {{
                            clearInterval(x);
                            document.getElementById("timer").innerHTML = "時間已到，車輛已駛離！";
                        }} else {{
                            var hours = Math.floor((distance % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
                            var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                            var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                            
                            var timeStr = "";
                            if(hours > 0) timeStr += hours + "時 ";
                            timeStr += minutes + "分 " + seconds + "秒";
                            document.getElementById("timer").innerHTML = "⏳ 剩餘 " + timeStr;
                        }}
                    }}, 1000);
                </script>
                """
                components.html(countdown_html, height=140)
            
            if not is_expired:
                st.write(f"**本段凍結票價**: NT$ {next_order['fare']}")
                total_pending_fare = sum(o["fare"] for o in pending_orders)

                if st.button("❌ 取消剩餘所有預約 (退回未扣款項)", use_container_width=True):
                    for o in user_data["history"]:
                        if o.get("status") == "pending":
                            user_data["balance"] += o["fare"]
                            user_data["frozen_balance"] -= o["fare"]
                            o["status"] = "canceled"
                    save_db(db)
                    st.toast(f"✅ 已成功取消後續行程，共解凍退回 NT$ {total_pending_fare}！", icon="💸")
                    time.sleep(1.5)
                    st.rerun()
        else:
            loc_col1, loc_col2 = st.columns(2)
            with loc_col1:
                start_loc = st.text_input("📍 出發地", placeholder="例如：磐石中學")
            with loc_col2:
                end_loc = st.text_input("📍 目的地", placeholder="例如：新竹火車站")
            
            mode = st.radio("選擇查詢模式", [
                "⚡ 即時查詢 (馬上出發)", 
                "🕒 特定查詢 (同時設定出發與到達時間)"
            ], horizontal=True)

            selected_date = None
            selected_start_time = None
            selected_end_time = None

            if mode == "🕒 特定查詢 (同時設定出發與到達時間)":
                with st.container(border=True):
                    st.markdown("⚙️ **行程時間範圍設定**")
                    selected_date = st.date_input("📅 選擇日期")
                    
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
                        st.write("💡 **詳細搭乘路線**")
                        
                    st.write(f"🕒 總車程預估：**{data['travel_time']}**")

                    for leg in data["transit_legs"]:
                        if leg["type"] == "WALKING":
                            st.info(f"🚶 **步行 ({leg['duration']})** : {leg['instruction']}")
                        elif leg["type"] == "TRANSIT":
                            with st.container(border=True):
                                col1, col2 = st.columns([2, 1])
                                with col1:
                                    st.markdown(f"**🚌 {leg['bus_name']}**")
                                with col2:
                                    bus_eta = data.get("eta", "正常營運")
                                    st.markdown(f"<div style='text-align:right; color:#28a745; font-size:14px; font-weight:bold;'>🟢 {bus_eta}</div>", unsafe_allow_html=True)
                                
                                t_col1, t_col2, t_col3 = st.columns([3, 2, 3])
                                with t_col1:
                                    st.markdown(f"<h3 style='margin-bottom:0px; padding-bottom:0px;'>{leg['dep_time']}</h3><span style='color:gray; font-size:14px;'>{leg['board']}</span>", unsafe_allow_html=True)
                                with t_col2:
                                    st.markdown(f"<div style='text-align:center; color:#888; margin-top:15px; font-size:13px;'>━━ {leg['num_stops']}站 ━━<br>{leg['duration']}</div>", unsafe_allow_html=True)
                                with t_col3:
                                    st.markdown(f"<h3 style='margin-bottom:0px; padding-bottom:0px; text-align:right;'>{leg['arr_time']}</h3><div style='text-align:right;'><span style='color:gray; font-size:14px;'>{leg['alight']}</span></div>", unsafe_allow_html=True)
                    
                    st.write("") 

                    if "coords" in data and not data["coords"].empty:
                        coords_df = data["coords"].copy()
                        colors = ["#007bff"] * len(coords_df) 
                        sizes = [40] * len(coords_df)         
                        
                        if len(coords_df) > 0:
                            colors[0] = "#28a745" 
                            sizes[0] = 150
                        if len(coords_df) > 1:
                            colors[-1] = "#dc3545" 
                            sizes[-1] = 150
                            
                        coords_df["color"] = colors
                        coords_df["size"] = sizes
                        
                        st.caption("🗺️ **路線導覽** ( 🟢起點 ➔ 🔵轉乘/途經 ➔ 🔴終點 )")
                        st.map(coords_df, color="color", size="size")
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
                                
                                if mode != "⚡ 即時查詢 (馬上出發)" and selected_date:
                                    journey_date_str = selected_date.strftime("%Y-%m-%d")
                                else:
                                    journey_date_str = time.strftime("%Y-%m-%d")

                                if num_legs > 0:
                                    fare_per_leg = actual_fare // num_legs
                                    remainder = actual_fare % num_legs
                                    
                                    for i, leg in enumerate(transit_legs):
                                        leg_fare = fare_per_leg + (remainder if i == 0 else 0)
                                        # 🌟 強制過濾時間格式，確保寫入資料庫的時間永遠是安全的 24 小時制！
                                        safe_time = extract_24h_time(leg['dep_time'])
                                        dep_datetime_str = f"{journey_date_str} {safe_time}"
                                        
                                        new_order = {
                                            "route": f"【{leg['bus_name']}】 {leg['board']} ➔ {leg['alight']}",
                                            "fare": leg_fare,
                                            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                            "dep_datetime": dep_datetime_str,
                                            "status": "pending"
                                        }
                                        user_data["history"].append(new_order)
                                else:
                                    new_order = {
                                        "route": st.session_state.search_title,
                                        "fare": actual_fare,
                                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "dep_datetime": time.strftime("%Y-%m-%d %H:%M:%S"),
                                        "status": "pending"
                                    }
                                    user_data["history"].append(new_order)

                                save_db(db)

                                st.session_state.pop("route_data", None)
                                st.session_state.pop("search_title", None)
                                st.session_state.pop("dyn_start", None)
                                st.session_state.pop("dyn_end", None)
                                
                                st.toast("🎉 分段預約成功！各段車資已凍結，請依序上車刷臉扣款。", icon="✅")
                                time.sleep(1.5)
                                st.rerun()
                            else:
                                st.error(f"❌ 可用餘額不足！您的餘額為 NT$ {user_data['balance']}，需 NT$ {actual_fare}。請先儲值。")

    # ==========================================
    # 第二頁籤：歷史訂單紀錄
    # ==========================================
    with tab2:
        st.markdown("### 📜 歷史訂單紀錄")
        
        if not user_data.get("history"):
            st.info("尚無任何訂單紀錄，趕快去預約一趟旅程吧！")
        else:
            for order in reversed(user_data["history"]):
                with st.container(border=True):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{order['route']}**")
                        st.caption(f"🕒 下單時間：{order['time']}")
                    with col2:
                        st.markdown(f"<div style='text-align:right; font-size:16px; font-weight:bold;'>NT$ {order['fare']}</div>", unsafe_allow_html=True)
                        
                        if order.get("status") == "pending":
                            st.markdown("<div style='text-align:right; color:#ffc107; font-size:14px; font-weight:bold;'>⏳ 待搭乘</div>", unsafe_allow_html=True)
                        elif order.get("status") == "completed":
                            st.markdown("<div style='text-align:right; color:#28a745; font-size:14px; font-weight:bold;'>✅ 已完成扣款</div>", unsafe_allow_html=True)
                        elif order.get("status") == "canceled":
                            st.markdown("<div style='text-align:right; color:#6c757d; font-size:14px; font-weight:bold;'>❌ 已取消</div>", unsafe_allow_html=True)
                        elif order.get("status") == "missed":
                            st.markdown("<div style='text-align:right; color:#dc3545; font-size:14px; font-weight:bold;'>🚫 違約未搭乘</div>", unsafe_allow_html=True)
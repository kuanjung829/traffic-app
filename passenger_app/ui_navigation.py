import streamlit as st
import time
from database import save_db

def render_navigation(db, user_email):
    user_data = db["users"][user_email]

    if "frozen_balance" not in user_data:
        user_data["frozen_balance"] = 0
    if "history" not in user_data:
        user_data["history"] = []

    # 檢查是否有未完成訂單
    pending_orders = [o for o in user_data["history"] if o.get("status") == "pending"]

    if pending_orders:
        st.subheader("📍 智能路線與預約搭乘")
        active_order = pending_orders[-1]
        st.warning("⚠️ 您目前有一筆尚未搭乘的預約訂單！請先完成搭乘或取消預約。")
        st.write(f"**預約路線**: {active_order['route']}")
        st.write(f"**凍結票價**: NT$ {active_order['fare']}")
        st.write(f"**下單時間**: {active_order['time']}")

        if st.button("❌ 取消預約 (退回凍結款項)", use_container_width=True):
            user_data["balance"] += active_order["fare"]
            user_data["frozen_balance"] -= active_order["fare"]
            active_order["status"] = "canceled"
            save_db(db)
            st.success("✅ 已成功取消訂單，款項已解凍並退回可用餘額！")
            time.sleep(1)
            st.rerun()
    else:
        # 完全還原你原本的介面設計
        st.subheader("📍 智能路線與預約搭乘")

        start_loc = st.text_input("📍 出發地", placeholder="例如：清華大學")
        end_loc = st.text_input("📍 目的地", placeholder="例如：新竹火車站")
        
        mode = st.radio("選擇查詢模式", ["⚡ 即時查詢 (馬上出發)", "🕒 預約查詢 (同時設定出發與到達時間)"])

        # 🌟 幫你把舊版被刪掉的時間選擇器完整加回來了
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
                # 根據選擇的模式，儲存不同的查詢結果字串
                if mode == "🕒 預約查詢 (同時設定出發與到達時間)":
                    st.session_state.search_route = f"{start_loc} ➔ {end_loc} ({selected_date} {selected_time} 出發)"
                else:
                    st.session_state.search_route = f"{start_loc} ➔ {end_loc} (即時出發)"

        # 顯示查詢結果與確認預約按鈕
        if "search_route" in st.session_state:
            st.markdown("---")
            st.write(f"### 查詢結果：{st.session_state.search_route}")

            base_fare = 15
            actual_fare = int(base_fare * 0.8) if user_data.get("is_student") else base_fare
            st.info(f"此路線預估票價： NT$ {actual_fare}")

            if st.button("✅ 確認預約 (凍結票價)", use_container_width=True):
                if user_data["balance"] >= actual_fare:
                    user_data["balance"] -= actual_fare
                    user_data["frozen_balance"] += actual_fare

                    new_order = {
                        "route": st.session_state.search_route,
                        "fare": actual_fare,
                        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "status": "pending"
                    }
                    user_data["history"].append(new_order)
                    save_db(db)

                    del st.session_state.search_route 
                    st.success("🎉 預約成功！款項已暫時凍結，上車刷臉時才會正式扣款。")
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error(f"❌ 可用餘額不足！您的餘額為 NT$ {user_data['balance']}，需 NT$ {actual_fare}。請先儲值。")
# passenger_app/ui_navigation.py
import streamlit as st
import time
from database import save_db

def render_navigation(db, user_email):
    st.subheader("📍 智能路線與預約搭乘")
    user_data = db["users"][user_email]
    
    # 初始化防呆：確保資料庫有凍結餘額與歷史紀錄欄位
    if "frozen_balance" not in user_data:
        user_data["frozen_balance"] = 0
    if "history" not in user_data:
        user_data["history"] = []

    # 💰 顯示最新錢包狀態
    col1, col2 = st.columns(2)
    col1.metric("💰 可用餘額", f"NT$ {user_data['balance']}")
    col2.metric("❄️ 凍結款項 (預約中)", f"NT$ {user_data['frozen_balance']}")
    st.markdown("---")

    # 🔍 尋找是否有一筆「等待搭乘 (pending)」的訂單
    pending_orders = [o for o in user_data["history"] if o.get("status") == "pending"]

    if pending_orders:
        active_order = pending_orders[-1] # 抓取最近一筆訂單
        st.warning("⚠️ 您目前有一筆尚未搭乘的預約訂單！請先完成搭乘或取消預約。")
        st.write(f"**預約路線**: {active_order['route']}")
        st.write(f"**凍結票價**: NT$ {active_order['fare']}")
        st.write(f"**下單時間**: {active_order['time']}")
        
        if st.button("❌ 取消預約 (退回凍結款項)", use_container_width=True):
            # 🔄 解除凍結：把錢從凍結區扣除，還給可用餘額
            user_data["balance"] += active_order["fare"]
            user_data["frozen_balance"] -= active_order["fare"]
            active_order["status"] = "canceled"  # 標記訂單為已取消
            
            save_db(db)
            st.success("✅ 已成功取消訂單，款項已解凍並退回可用餘額！")
            time.sleep(1)
            st.rerun()
    else:
        # 🆕 沒有訂單時，顯示預約介面
        st.write("### 🆕 新增乘車預約")
        route = st.selectbox("選擇預計搭乘路線", ["藍1區間車 (清大-火車站)", "綠線公車 (交大-高鐵站)", "紅線公車 (市區環狀)"])
        
        base_fare = 15
        actual_fare = int(base_fare * 0.8) if user_data.get("is_student") else base_fare
        st.info(f"此路線預估票價： **NT$ {actual_fare}**")
        
        if st.button("✅ 確認預約 (凍結票價)", use_container_width=True):
            if user_data["balance"] >= actual_fare:
                # 🔒 執行凍結：從可用餘額扣除，移入凍結餘額
                user_data["balance"] -= actual_fare
                user_data["frozen_balance"] += actual_fare
                
                new_order = {
                    "route": route,
                    "fare": actual_fare,
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "status": "pending"  # 關鍵標記：等待搭乘
                }
                user_data["history"].append(new_order)
                
                save_db(db)
                st.success("🎉 預約成功！款項已暫時凍結，上車刷臉時才會正式扣款。")
                time.sleep(1.5)
                st.rerun()
            else:
                st.error(f"❌ 可用餘額不足！您的餘額為 NT$ {user_data['balance']}，需 NT$ {actual_fare}。請先儲值。")
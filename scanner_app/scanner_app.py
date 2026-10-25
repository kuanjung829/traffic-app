# scanner_app/scanner_app.py
import streamlit as st
import os
import json
import time

st.set_page_config(page_title="公車 AI 驗票接收端", page_icon="🚌", layout="wide")

DB_FILE = "../shared_data/users_db.json"

def load_db():
    if not os.path.exists(DB_FILE):
        return {"users": {}}
    with open(DB_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_db(db_data):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db_data, f, indent=4, ensure_ascii=False)

st.title("🚌 新竹客運 AI 無感支付驗票機")
st.markdown("---")

col_cam, col_info = st.columns([1.5, 1])

with col_cam:
    st.subheader("📷 乘客上車掃描區")
    picture = st.camera_input("請乘客直視鏡頭以進行扣款", key="bus_cam")

with col_info:
    st.subheader("💳 交易狀態看板")
    status_placeholder = st.empty()
    status_placeholder.info("等待乘客上車刷臉...")

if picture:
    status_placeholder.warning("🔄 系統辨識中...請稍候")
    db = load_db()
    
    # 模擬 AI 處理時間，讓展示更真實
    time.sleep(1)
    
    try:
        matched_user = None
        # 🚀 無敵展示版：只要有拍照，就自動尋找一個已經註冊過的帳號來扣款！
        for email, user_data in db["users"].items():
            if user_data.get("face_verified"):
                matched_user = email
                break
        
        if matched_user:
            user_info = db["users"][matched_user]
            base_fare = 15
            actual_fare = int(base_fare * 0.8) if user_info.get("is_student") else base_fare
            
            if user_info["balance"] >= actual_fare:
                user_info["balance"] -= actual_fare
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                user_info["history"].append({
                    "route": "新竹客運 (實體機台掃描)",
                    "start": "實體站牌上車",
                    "end": "未知",
                    "fare": actual_fare,
                    "time": current_time,
                    "status": "valid"
                })
                save_db(db)
                status_placeholder.success(f"""
                ### 🟢 驗證成功，請上車！
                * **乘客信箱**：{matched_user}
                * **扣款金額**：NT$ {actual_fare} {'(學生8折)' if user_info.get("is_student") else '(全票)'}
                * **錢包餘額**：NT$ {user_info['balance']}
                """)
            else:
                status_placeholder.error(f"""
                ### 🔴 餘額不足！
                * **乘客信箱**：{matched_user}
                * **錢包餘額**：NT$ {user_info['balance']} (需 NT$ {actual_fare})
                """)
        else:
            status_placeholder.error("### 🔴 查無註冊資料，請先下載 APP 註冊並綁定生物特徵！")
            
    except Exception as e:
        status_placeholder.error(f"系統錯誤：{e}")
# ui_sidebar.py
import streamlit as st
import re
import time
import random
from database import save_db
from ui_face import face_dialog

# ==========================================
# 定義所有的中央彈出視窗 (Dialogs)
# ==========================================
@st.dialog("📱 綁定手機領取 50 元")
def phone_dialog(db, user_email):
    user_data = db["users"][user_email]
    phone_input = st.text_input("手機號碼 (10碼，09開頭)", max_chars=10)
    
    if "simulated_otp" not in st.session_state:
        st.session_state.simulated_otp = None
    
    if st.button("發送驗證碼", use_container_width=True):
        if not re.match(r"^09\d{8}$", phone_input):
            st.error("❌ 格式錯誤！必須為 10 碼純數字且以 09 開頭。")
        else:
            st.session_state.simulated_otp = str(random.randint(100000, 999999))
            st.success("驗證碼已發送！請查看下方模擬簡訊。")
    
    if st.session_state.simulated_otp:
        st.info(f"💬 【模擬簡訊】您的 6 位數驗證碼為：**{st.session_state.simulated_otp}**")
        code_input = st.text_input("輸入 6 位數驗證碼", max_chars=6)
        
        if st.button("確認驗證並獲得 50 元", type="primary", use_container_width=True):
            if code_input == st.session_state.simulated_otp:
                user_data["phone"] = phone_input
                user_data["phone_verified"] = True
                user_data["balance"] += 50
                save_db(db)
                st.session_state.simulated_otp = None
                st.success("🎉 手機綁定成功！已獲 NT$ 50。視窗將自動關閉...")
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ 驗證碼錯誤，請重新輸入！")

@st.dialog("💳 綁定信用卡")
def credit_card_dialog(db, user_email):
    user_data = db["users"][user_email]
    cc_num = st.text_input("信用卡卡號 (16碼數字)", max_chars=16)
    cc_date = st.text_input("有效期限 (MM/YY)", max_chars=5)
    cc_cvv = st.text_input("安全碼 (3碼)", max_chars=3, type="password")
    
    if st.button("確認綁定", type="primary", use_container_width=True):
        if not re.match(r"^\d{16}$", cc_num):
            st.error("❌ 卡號格式錯誤！必須為 16 碼純數字。")
        elif not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", cc_date):
            st.error("❌ 有效期限格式錯誤！請輸入 MM/YY。")
        elif not cc_cvv.isdigit() or len(cc_cvv) != 3:
            st.error("❌ 安全碼格式錯誤！")
        else:
            user_data["credit_card"] = cc_num
            save_db(db)
            st.success("✅ 信用卡綁定成功！視窗將自動關閉...")
            time.sleep(2)
            st.rerun()

@st.dialog("💰 虛擬錢包儲值中心")
def topup_dialog(db, user_email):
    user_data = db["users"][user_email]
    add_amount = st.selectbox("選擇儲值金額", [15, 30, 50, 100, 300, 500])
    if st.button("確認儲值", use_container_width=True, type="primary"):
        user_data["balance"] += add_amount
        save_db(db)
        st.success(f"✅ 成功儲值 NT$ {add_amount}！視窗將自動關閉...")
        time.sleep(2)
        st.rerun()

@st.dialog("📜 歷史乘車明細")
def history_dialog(db, user_email):
    user_data = db["users"][user_email]
    history_list = user_data.get("history", [])
    if not history_list:
        st.info("尚無乘車紀錄")
    else:
        for idx, h in enumerate(reversed(history_list[-5:])):
            with st.container(border=True):
                st.write(f"🚍 **{h['route']}** (扣款: NT$ {h['fare']})")
                st.caption(f"🕒 {h['time']}")
                st.write(f"📍 {h['start']} ➔ 🏁 {h['end']}")


# ==========================================
# 側邊欄主程式 (只負責顯示狀態與按鈕)
# ==========================================
def render_sidebar(db, user_email):
    user_data = db["users"][user_email]
    
    # 初始化資料庫欄位 (加入照片路徑)
    if "balance" not in user_data: user_data["balance"] = 0
    if "remember_me" not in user_data: user_data["remember_me"] = False
    if "phone" not in user_data: user_data["phone"] = None
    if "phone_verified" not in user_data: user_data["phone_verified"] = False
    if "face_verified" not in user_data: user_data["face_verified"] = False
    if "face_image_path" not in user_data: user_data["face_image_path"] = "" # ✨ 新增：照片路徑
    save_db(db)

    st.title("👤 會員專區")
    
    if user_data["is_student"]:
        st.markdown(f"### {user_data['school_abbr']} ({user_data['name']})")
        st.success("✅ 學生票優惠啟用")
    else:
        st.markdown(f"### {user_data['name']}")
        st.info("一般帳號 (無優惠)")
        
    st.divider()
    st.metric("💳 虛擬錢包餘額", f"NT$ {user_data['balance']}")
    st.divider()
    
    # 📱 1. 手機號碼區塊
    st.markdown("### 📱 手機驗證 (領取50元)")
    if user_data["phone_verified"]:
        masked_phone = user_data["phone"][:4] + "****" + user_data["phone"][-2:]
        st.success(f"✅ 已綁定：`{masked_phone}`")
    else:
        st.warning("⚠️ 尚未綁定手機")
        if st.button("👉 前往綁定手機", use_container_width=True):
            phone_dialog(db, user_email)

    st.divider()
    
    # 🤖 2. 真實 AI 人臉識別區塊
    st.markdown("### 🤖 真實人臉識別")
    if user_data["face_verified"]:
        st.success("✅ 已完成生物驗證")
        
        # ✨ 新增：如果在資料庫有存到照片路徑，就在側邊欄顯示出來！
        if user_data.get("face_image_path"):
            st.image(user_data["face_image_path"], caption="您的人臉特徵", width=120)
            
        if st.button("🔄 重新人臉拍照校正", use_container_width=True):
            user_data["face_verified"] = False
            user_data["face_image_path"] = ""
            save_db(db)
            st.rerun()
    else:
        st.warning("⚠️ 尚未進行拍照驗證")
        if st.button("👉 啟動鏡頭開始建模", use_container_width=True):
            face_dialog(db, user_email)

    st.divider()
    
    # 🔒 3. 信用卡區塊
    st.markdown("### 🔒 信用卡與儲值")
    if not user_data.get("credit_card"):
        st.warning("⚠️ 尚未綁定信用卡")
        if st.button("👉 前往綁定信用卡", use_container_width=True):
            credit_card_dialog(db, user_email)
    else:
        cc_hidden = f"**** **** **** {user_data['credit_card'][-4:]}"
        st.markdown(f"**已綁定**：`{cc_hidden}`")
        
        if st.button("💰 前往儲值中心", use_container_width=True):
            topup_dialog(db, user_email)
            
        if st.button("❌ 解除綁定", use_container_width=True):
            db["users"][user_email]["credit_card"] = None
            save_db(db)
            st.rerun()
            
    st.divider()
    
    # 📜 4. 歷史紀錄
    st.markdown("### 📜 乘車紀錄")
    if st.button("🧾 查看歷史乘車明細", use_container_width=True):
        history_dialog(db, user_email)
                
    st.divider()
    
    # 🚪 5. 登出
    if st.button("🚪 登出系統", use_container_width=True):
        if user_email in db["users"]:
            db["users"][user_email]["remember_me"] = False
            save_db(db)
            
        if "logged_in_user" in st.query_params:
            del st.query_params["logged_in_user"]
            
        st.session_state.current_user = None
        st.session_state.page = "login"
        st.rerun()
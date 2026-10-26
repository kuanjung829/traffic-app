import streamlit as st
import os
import time
from PIL import Image
from ui_face import face_dialog
from database import save_db

# 💳 綁定信用卡彈出視窗
@st.dialog("💳 綁定信用卡")
def credit_card_dialog(db, user_email):
    st.write("綁定信用卡後即可啟用線上儲值功能")
    card_num = st.text_input("信用卡卡號", placeholder="例如：4311-9522-2222-2222")
    valid_thru = st.text_input("有效期限 (MM/YY)", placeholder="例如：12/28")
    cvv = st.text_input("安全碼 (CVV)", type="password", max_chars=3)
    
    if st.button("確認綁定", use_container_width=True):
        if card_num and valid_thru and cvv:
            # 為了資安考量與展示，資料庫只儲存卡號後 4 碼
            db["users"][user_email]["credit_card"] = card_num[-4:]
            save_db(db)
            st.success("✅ 信用卡綁定成功！您現在可以使用儲值功能了。")
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("❌ 請完整填寫信用卡資訊")

# 💳 儲值系統彈出視窗
@st.dialog("💳 虛擬錢包儲值")
def recharge_dialog(db, user_email):
    st.write(f"使用已綁定信用卡 (尾數 {db['users'][user_email].get('credit_card')}) 進行扣款")
    amount = st.selectbox("選擇儲值金額", [100, 200, 500, 1000, 2000])
    if st.button("確認付款並儲值", use_container_width=True):
        db["users"][user_email]["balance"] += amount
        save_db(db)
        st.success(f"✅ 成功儲值 NT$ {amount}！")
        time.sleep(1.5)
        st.rerun()

# 📱 手機綁定彈出視窗
@st.dialog("📱 手機綁定與驗證")
def phone_dialog(db, user_email):
    st.write("完成手機綁定即可領取 NT$ 50 乘車金！")
    phone = st.text_input("請輸入手機號碼")
    if st.button("確認綁定", use_container_width=True):
        if phone:
            db["users"][user_email]["phone"] = phone
            db["users"][user_email]["balance"] += 50
            save_db(db)
            st.success("✅ 綁定成功！已發放 NT$ 50 乘車金。")
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("❌ 請輸入手機號碼")

def render_sidebar(db, user_email, controller):
    user_data = db["users"][user_email]

    st.sidebar.title("👤 會員專區")
    st.sidebar.write(f"**{user_data.get('name', '使用者')}** ({user_email})")

    if user_data.get("is_student"):
        st.sidebar.info(f"🎓 學生帳號 ({user_data.get('school_abbr', '已認證')})")
    else:
        st.sidebar.info("👤 一般帳號 (無優惠)")

    st.sidebar.divider() 

    # 💳 信用卡與儲值區塊
    st.sidebar.subheader("💳 信用卡與儲值")
    st.sidebar.metric(label="可用餘額", value=f"NT$ {user_data['balance']}")
    if user_data.get("frozen_balance", 0) > 0:
        st.sidebar.caption(f"❄️ 另有 NT$ {user_data['frozen_balance']} 預約凍結中")
    
    st.sidebar.write("")
    
    # 判斷是否已綁定信用卡，切換顯示的按鈕
    if user_data.get("credit_card"):
        st.sidebar.success(f"✅ 已綁定信用卡 (尾數 {user_data['credit_card']})")
        if st.sidebar.button("💰 前往儲值", use_container_width=True):
            recharge_dialog(db, user_email)
    else:
        st.sidebar.warning("⚠️ 尚未綁定信用卡")
        if st.sidebar.button("👉 前往綁定信用卡", use_container_width=True):
            credit_card_dialog(db, user_email)

    st.sidebar.divider()

    # 📱 手機驗證區塊
    st.sidebar.subheader("📱 手機驗證 (領取50元)")
    if user_data.get("phone"):
        st.sidebar.success(f"✅ 已綁定: {user_data['phone']}")
    else:
        st.sidebar.warning("⚠️ 尚未綁定手機")
        st.sidebar.write("") 
        if st.sidebar.button("👉 前往綁定手機", use_container_width=True):
            phone_dialog(db, user_email)

    st.sidebar.divider() 

    # 😁 人臉識別存檔狀態
    st.sidebar.subheader("😁 人臉識別存檔狀態")
    if user_data.get("face_verified"):
        st.sidebar.success("✅ 已完成生物驗證")
        
        face_path = f"../shared_data/face_photos/{user_email}.png"
        if os.path.exists(face_path):
            img = Image.open(face_path)
            st.sidebar.image(img, caption="您的人臉特徵", width=150)
        
        st.sidebar.write("")
        if st.sidebar.button("🔄 重新人臉拍照校正", use_container_width=True):
            face_dialog(db, user_email)
    else:
        st.sidebar.warning("⚠️ 尚未進行拍照驗證")
        st.sidebar.write("")
        if st.sidebar.button("📸 啟動鏡頭開始建模", use_container_width=True):
            face_dialog(db, user_email)

    st.sidebar.divider() 

    # 🧭 系統導覽
    st.sidebar.subheader("🧭 系統導覽")
    menu = st.sidebar.radio("選擇模式", ["預約與搭乘", "驗票機模擬"], label_visibility="collapsed")
    
    st.sidebar.write("") 
    if st.sidebar.button("🚪 登出系統", use_container_width=True):
        st.session_state.logged_in_user = None
        controller.remove("logged_in_user")
        st.sidebar.success("正在登出系統...")
        time.sleep(1.5)
        st.rerun()
        
    return menu
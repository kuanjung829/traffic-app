# passenger_app/ui_sidebar.py
import streamlit as st
import os
from PIL import Image
from ui_face import face_dialog

def render_sidebar(db, user_email):
    user_data = db["users"][user_email]

    st.sidebar.title("👤 會員專區")
    st.sidebar.write(f"**{user_data.get('name', '使用者')}** ({user_email})")

    # 🎓 身分標籤區塊
    if user_data.get("is_student"):
        st.sidebar.info(f"🎓 學生帳號 ({user_data.get('school_abbr', '已認證')})")
    else:
        st.sidebar.info("👤 一般帳號 (無優惠)")

    st.sidebar.divider()  # 🌟 加入分隔線，防止黏在一起

    # 💳 錢包區塊
    st.sidebar.subheader("💳 虛擬錢包餘額")
    st.sidebar.metric(label="可用餘額", value=f"NT$ {user_data['balance']}")
    if user_data.get("frozen_balance", 0) > 0:
        st.sidebar.caption(f"❄️ 另有 NT$ {user_data['frozen_balance']} 預約凍結中")

    st.sidebar.divider()  # 🌟 加入分隔線

    # 📱 手機驗證區塊
    st.sidebar.subheader("📱 手機驗證 (領取50元)")
    if user_data.get("phone"):
        st.sidebar.success(f"✅ 已綁定: {user_data['phone']}")
    else:
        st.sidebar.warning("⚠️ 尚未綁定手機")
        st.sidebar.write("") # 小留白
        if st.sidebar.button("👉 前往綁定手機", use_container_width=True):
            st.toast("手機綁定功能開發中！", icon="🛠️") # 避免按鈕沒反應，先放個提示

    st.sidebar.divider()  # 🌟 加入分隔線

    # 😁 人臉識別狀態區塊
    st.sidebar.subheader("😁 人臉識別存檔狀態")
    if user_data.get("face_verified"):
        st.sidebar.success("✅ 已完成生物驗證")
        
        # 顯示大頭貼
        face_path = f"../shared_data/face_photos/{user_email}.png"
        if os.path.exists(face_path):
            img = Image.open(face_path)
            st.sidebar.image(img, caption="您的人臉特徵", width=150)
        
        st.sidebar.write("") # 增加按鈕上方的呼吸空間
        if st.sidebar.button("🔄 重新人臉拍照校正", use_container_width=True):
            face_dialog(db, user_email)
    else:
        st.sidebar.warning("⚠️ 尚未進行拍照驗證")
        st.sidebar.write("") # 小留白
        if st.sidebar.button("📸 啟動鏡頭開始建模", use_container_width=True):
            face_dialog(db, user_email)

    st.sidebar.divider()  # 🌟 加入分隔線

    # 🧭 導覽列與登出
    st.sidebar.subheader("🧭 系統導覽")
    menu = st.sidebar.radio("選擇模式", ["預約與搭乘", "驗票機模擬"], label_visibility="collapsed")
    
    st.sidebar.write("") # 登出按鈕上方留白
    if st.sidebar.button("🚪 登出系統", use_container_width=True):
        st.session_state.logged_in_user = None
        st.rerun()
        
    return menu
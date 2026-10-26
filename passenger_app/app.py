# passenger_app/app.py
import streamlit as st
from database import load_db
from ui_auth import render_auth
from ui_sidebar import render_sidebar
from ui_navigation import render_navigation
from ui_scanner import render_scanner

st.set_page_config(page_title="AI 智慧公車無感支付", page_icon="🚌", layout="centered")

db = load_db()

# 💡 核心資安修正：強制使用 Streamlit 內建的獨立 Session State
# 絕對不從 users_db.json 讀取「保持登入」標記，徹底隔絕不同使用者的狀態
if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

if st.session_state.logged_in_user is None:
    # 尚未登入，顯示登入畫面
    render_auth(db)
else:
    # 已登入，進入系統
    user_email = st.session_state.logged_in_user
    menu = render_sidebar(db, user_email)
    
    # 根據側邊欄回傳的選項切換畫面
    if menu == "驗票機模擬":
        render_scanner(db)
    else:
        render_navigation(db, user_email)
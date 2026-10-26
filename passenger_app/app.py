import streamlit as st
from database import load_db
from ui_auth import render_auth
from ui_sidebar import render_sidebar
from ui_navigation import render_navigation
from ui_scanner import render_scanner
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="AI 智慧公車無感支付", page_icon="🚌", layout="centered")

# 初始化 Cookie 控制器
controller = CookieController()
db = load_db()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# 🌟 啟動時先檢查瀏覽器是否存有 Cookie
saved_user = controller.get("logged_in_user")
if saved_user and st.session_state.logged_in_user is None:
    st.session_state.logged_in_user = saved_user

if st.session_state.logged_in_user is None:
    # 把控制器傳給驗證頁面，以便登入時寫入 Cookie
    render_auth(db, controller)
else:
    user_email = st.session_state.logged_in_user
    # 把控制器傳給側邊欄，以便登出時刪除 Cookie
    menu = render_sidebar(db, user_email, controller)
    
    if menu == "驗票機模擬":
        render_scanner(db)
    else:
        render_navigation(db, user_email)
import streamlit as st
import os
import time

# 🌟 關鍵修復：強制將雲端主機的時區切換為台灣時間 (UTC+8)
os.environ['TZ'] = 'Asia/Taipei'
if hasattr(time, 'tzset'):
    time.tzset()

from database import load_db
from ui_auth import render_auth
from ui_sidebar import render_sidebar
from ui_navigation import render_navigation
from ui_scanner import render_scanner
from streamlit_cookies_controller import CookieController

st.set_page_config(page_title="AI 智慧公車無感支付", page_icon="🚌", layout="centered")

# 🌟 UI 優化 第一彈：隱藏 Streamlit 預設框架，打造原生 APP 沉浸感
hide_st_style = """
            <style>
            #MainMenu {visibility: hidden;} /* 隱藏右上角漢堡選單 */
            footer {visibility: hidden;}    /* 隱藏底部 Made with Streamlit */
            
            /* 微調主畫面的頂部間距，讓它更像手機 App 的版面 */
            .block-container {
                padding-top: 2rem;
                padding-bottom: 2rem;
            }
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# 初始化 Cookie 控制器
controller = CookieController()
db = load_db()

if "logged_in_user" not in st.session_state:
    st.session_state.logged_in_user = None

# 啟動時先檢查瀏覽器是否存有 Cookie
saved_user = controller.get("logged_in_user")
if saved_user and st.session_state.logged_in_user is None:
    st.session_state.logged_in_user = saved_user

if st.session_state.logged_in_user is None:
    render_auth(db, controller)
else:
    user_email = st.session_state.logged_in_user
    menu = render_sidebar(db, user_email, controller)
    
    if menu == "驗票機模擬":
        render_scanner(db)
    else:
        render_navigation(db, user_email)
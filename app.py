import streamlit as st
from database import load_db

from ui_auth import render_auth_page
from ui_sidebar import render_sidebar
# 確保我們在這裡同時引入了兩個 tab 的函式
from ui_navigation import render_navigation_tab, render_nearby_tab 

db = load_db()

st.set_page_config(page_title="AI 智慧公車系統", page_icon="🚌", layout="wide")

# UI 美化 CSS 魔法
def set_custom_css():
    st.markdown("""
        <style>
        .stAppDeployButton {display:none;}
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        .stButton>button {
            border-radius: 20px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            transition: all 0.3s ease-in-out;
        }
        .stButton>button:hover {
            transform: scale(1.03);
            box-shadow: 0 4px 10px rgba(0,0,0,0.15);
        }

        [data-testid="stSidebar"] {
            box-shadow: 3px 0 10px rgba(0,0,0,0.05);
        }
        
        div[data-testid="stVerticalBlock"] > div[style*="border"] {
            border-radius: 15px !important;
            border: 1px solid #E0E5EC !important;
            box-shadow: 0 4px 8px rgba(0,0,0,0.03) !important;
            background-color: #FFFFFF;
        }
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

# ==========================================
# 頁面路由器 (Router)
# ==========================================
if "page" not in st.session_state: st.session_state.page = "login"
if "current_user" not in st.session_state: st.session_state.current_user = None

# 自動登入檢查
if not st.session_state.current_user:
    saved_email = st.query_params.get("logged_in_user")
    if saved_email and saved_email in db["users"]:
        if db["users"][saved_email].get("remember_me", False):
            st.session_state.current_user = saved_email
            st.session_state.page = "dashboard"

if st.session_state.page == "login":
    render_auth_page(db)
    
elif st.session_state.page == "dashboard":
    user_email = st.session_state.current_user
    
    with st.sidebar:
        render_sidebar(db, user_email)

    st.title("選擇搭乘交通工具")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🚌\n\n公車系統", use_container_width=True, type="primary"): pass
    with col2: st.button("🚇\n\n捷運 (敬請期待)", use_container_width=True, disabled=True)
    with col3: st.button("🚂\n\n火車 (敬請期待)", use_container_width=True, disabled=True)
    with col4: st.button("🚲\n\nYouBike (敬請期待)", use_container_width=True, disabled=True)
    
    st.divider()
    
    # 這裡確保只會畫出「一次」分頁
    tab1, tab2 = st.tabs(["導航：目前地 ➔ 目的地", "📍 附近站牌與路線"])
    
    with tab1: 
        render_navigation_tab(db, user_email)
        
    with tab2: 
        render_nearby_tab()
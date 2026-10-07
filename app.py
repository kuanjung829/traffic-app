import streamlit as st
from database import load_db

# 匯入所有的 UI 模組，分工合作
from ui_auth import render_auth_page
from ui_sidebar import render_sidebar
from ui_navigation import render_navigation_tab

db = load_db()

st.set_page_config(page_title="AI 智慧公車系統", page_icon="🚌", layout="wide")

if "page" not in st.session_state: st.session_state.page = "login"
if "current_user" not in st.session_state: st.session_state.current_user = None

# ==========================================
# 頁面路由器 (Router)
# ==========================================
if st.session_state.page == "login":
    render_auth_page(db)
    
elif st.session_state.page == "dashboard":
    user_email = st.session_state.current_user
    
    # --- 1. 左側會員專區 (呼叫 sidebar 模組) ---
    with st.sidebar:
        render_sidebar(db, user_email)

    # --- 2. 右側主畫面 (交通工具選項) ---
    st.title("選擇搭乘交通工具")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🚌\n\n公車系統", use_container_width=True, type="primary"): pass
    with col2: st.button("🚇\n\n捷運 (敬請期待)", use_container_width=True, disabled=True)
    with col3: st.button("🚂\n\n火車 (敬請期待)", use_container_width=True, disabled=True)
    with col4: st.button("🚲\n\nYouBike (敬請期待)", use_container_width=True, disabled=True)
    
    st.divider()
    
    # --- 3. 下方功能分頁 ---
    # 因為信用卡移到左邊了，這裡只需要保留兩個 Tab
    tab1, tab2 = st.tabs(["導航：目前地 ➔ 目的地", "📍 附近站牌與路線"])
    
    with tab1: 
        render_navigation_tab(db, user_email)
        
    with tab2: 
        st.info("🚧 此功能還在開發中，敬請期待！將來可直接顯示附近站牌動態。")
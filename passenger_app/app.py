# passenger_app/app.py
import streamlit as st
from database import load_db

# 匯入你的 UI 元件
from ui_sidebar import render_sidebar
from ui_scanner import render_scanner
from ui_auth import render_auth_page
from ui_navigation import render_navigation_tab

# 設定網頁標題與寬度
st.set_page_config(page_title="磐石高中 AI 公車系統", page_icon="🚌", layout="wide")

def main():
    # 1. 載入資料庫
    db = load_db()

    # 2. 💡 初始化 Session State：加入「保持登入」自動偵測機制
    if "current_user" not in st.session_state:
        # 先預設為未登入
        st.session_state.current_user = None
        st.session_state.page = "login"
        
        # 去資料庫掃描，看看有沒有人之前勾選了「保持登入」
        for email, user_data in db["users"].items():
            if user_data.get("remember_me") == True:
                # 找到了！直接幫他自動登入
                st.session_state.current_user = email
                st.session_state.page = "dashboard"
                break  # 找到就跳出迴圈

    # 3. 頁面路由切換
    
    # 登入頁面
    if st.session_state.page == "login":
        render_auth_page(db)

    # 🌟 專題展示：公車驗票機模式
    elif st.session_state.page == "scanner_mode":
        render_scanner(db)
        
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("⬅️ 結束機台模擬，返回乘客端 APP", use_container_width=True):
                st.session_state.page = "dashboard"
                st.rerun()

    # 主系統 (乘客端)
    else:
        if st.session_state.current_user:
            user_email = st.session_state.current_user
            
            with st.sidebar:
                render_sidebar(db, user_email)
            
            render_navigation_tab(db, user_email)
            
        else:
            st.session_state.page = "login"
            st.rerun()

if __name__ == "__main__":
    main()
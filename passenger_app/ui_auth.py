# passenger_app/ui_auth.py
import streamlit as st
from database import save_db

def render_auth(db):
    st.title("🚌 AI 智慧公車無感支付系統")
    st.caption("安全支付：登入狀態獨立隔離，不與他人共用")
    
    tab1, tab2 = st.tabs(["🔑 會員登入", "📝 註冊新帳號"])
    
    with tab1:
        email = st.text_input("電子郵件 (帳號)", key="login_email")
        pwd = st.text_input("密碼", type="password", key="login_pwd")
        
        # 💡 移除了將「保持登入」寫入雲端資料庫的危險邏輯
        if st.button("🚀 登入系統", use_container_width=True):
            if email in db["users"] and db["users"][email].get("pwd") == pwd:
                # 🔒 核心資安修正：只在「當前使用者的獨立瀏覽器 Session」中標記登入
                st.session_state.logged_in_user = email
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤！")
                
    with tab2:
        reg_email = st.text_input("註冊信箱", key="reg_email")
        reg_name = st.text_input("真實姓名", key="reg_name")
        reg_pwd = st.text_input("設定密碼", type="password", key="reg_pwd")
        is_student = st.checkbox("我是學生 (享有票價優惠)")
        
        if st.button("📝 註冊帳號", use_container_width=True):
            if reg_email in db["users"]:
                st.error("❌ 此信箱已被註冊！")
            elif not reg_email or not reg_pwd or not reg_name:
                st.error("❌ 請完整填寫資料！")
            else:
                db["users"][reg_email] = {
                    "name": reg_name,
                    "pwd": reg_pwd,
                    "is_student": is_student,
                    "balance": 0,
                    "frozen_balance": 0,
                    "face_verified": False,
                    "history": []
                }
                save_db(db)
                st.success("🎉 註冊成功！請切換至登入分頁。")
import streamlit as st
from database import save_db

def render_auth(db):
    st.title("🚌 AI 智慧公車無感支付系統")
    
    choice = st.radio("請選擇操作", ["登入", "註冊新帳號"], horizontal=True)
    
    if choice == "登入":
        email = st.text_input("信箱帳號", key="login_email")
        pwd = st.text_input("密碼", type="password", key="login_pwd")
        remember_me = st.checkbox("保持登入")
        
        if st.button("登入", use_container_width=True):
            if email in db["users"] and db["users"][email].get("pwd") == pwd:
                st.session_state.logged_in_user = email
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤！")
                
    elif choice == "註冊新帳號":
        reg_name = st.text_input("使用者名稱", key="reg_name")
        # 提示使用者可以使用教育信箱
        reg_email = st.text_input("信箱帳號 (使用 .edu.tw 結尾信箱自動享有學生優惠)", key="reg_email")
        reg_pwd = st.text_input("密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("確認密碼", type="password", key="reg_pwd_confirm")
        
        if st.button("註冊", use_container_width=True):
            if reg_email in db["users"]:
                st.error("❌ 此信箱已被註冊！")
            elif not reg_email or not reg_pwd or not reg_name or not reg_pwd_confirm:
                st.error("❌ 請完整填寫基本資料！")
            elif reg_pwd != reg_pwd_confirm:
                st.error("❌ 兩次輸入的密碼不一致！")
            else:
                # 🎓 自動判斷學生身分：檢查信箱是否以 .edu.tw 結尾 (包含 .hc.edu.tw)
                is_student = reg_email.strip().lower().endswith(".edu.tw")
                school_abbr = "教育局認證學校" if is_student else ""
                
                db["users"][reg_email] = {
                    "name": reg_name,
                    "pwd": reg_pwd,
                    "is_student": is_student,
                    "school_abbr": school_abbr,
                    "balance": 0,
                    "frozen_balance": 0,
                    "face_verified": False,
                    "history": []
                }
                save_db(db)
                
                # 根據身分給予不同的成功提示
                if is_student:
                    st.success("🎉 註冊成功！系統已透過教育信箱自動為您開通學生優惠，請點選上方「登入」。")
                else:
                    st.success("🎉 註冊成功！請點選上方「登入」進行操作。")
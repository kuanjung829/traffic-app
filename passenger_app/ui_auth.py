import streamlit as st
from database import save_db

def render_auth(db, controller):
    st.title("🚌 AI 智慧公車無感支付系統")
    
    choice = st.radio("請選擇操作", ["登入", "註冊新帳號"], horizontal=True)
    
    if choice == "登入":
        email = st.text_input("Gmail (信箱)", key="login_email")
        pwd = st.text_input("密碼", type="password", key="login_pwd")
        remember_me = st.checkbox("保持登入")
        
        if st.button("登入", use_container_width=True):
            if email in db["users"] and db["users"][email].get("pwd") == pwd:
                st.session_state.logged_in_user = email
                
                # 🌟 如果勾選保持登入，寫入瀏覽器 Cookie (保存 30 天)
                if remember_me:
                    controller.set("logged_in_user", email, max_age=30*24*60*60)
                    
                st.success("登入成功！")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤！")
                
    elif choice == "註冊新帳號":
        reg_name = st.text_input("使用者名稱", key="reg_name")
        reg_email = st.text_input("Gmail (信箱)", key="reg_email")
        reg_pwd = st.text_input("密碼", type="password", key="reg_pwd")
        reg_pwd_confirm = st.text_input("確認密碼", type="password", key="reg_pwd_confirm")
        
        is_student = st.checkbox("我是學生 (享有票價優惠)")
        school_abbr = ""
        if is_student:
            school_abbr = st.text_input("請輸入學校簡稱 (例如：磐石高中)", key="reg_school")
            
        if st.button("註冊", use_container_width=True):
            if reg_email in db["users"]:
                st.error("❌ 此信箱已被註冊！")
            elif not reg_email or not reg_pwd or not reg_name or not reg_pwd_confirm:
                st.error("❌ 請完整填寫基本資料！")
            elif reg_pwd != reg_pwd_confirm:
                st.error("❌ 兩次輸入的密碼不一致！")
            elif is_student and not school_abbr:
                st.error("❌ 勾選學生身分請務必填寫學校簡稱！")
            else:
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
                st.success("🎉 註冊成功！請點選上方「登入」進行操作。")
# ui_auth.py
import streamlit as st
from database import save_db

def render_auth_page(db):
    st.title("🚌 AI 智慧公車無感支付系統")
    auth_mode = st.radio("請選擇操作", ["登入", "註冊新帳號"], horizontal=True)
    
    if auth_mode == "登入":
        with st.form("login_form"):
            email = st.text_input("Gmail (帳號)")
            pwd = st.text_input("密碼", type="password")
            remember_me = st.checkbox("保持登入 (記住我的裝置)")
            
            submitted = st.form_submit_button("登入", type="primary")
            if submitted:
                if email in db["users"] and db["users"][email]["pwd"] == pwd:
                    db["users"][email]["remember_me"] = remember_me
                    save_db(db)
                    
                    st.session_state.current_user = email
                    st.session_state.page = "dashboard"
                    
                    if remember_me:
                        st.query_params["logged_in_user"] = email
                    else:
                        if "logged_in_user" in st.query_params:
                            del st.query_params["logged_in_user"]
                            
                    st.rerun()
                else:
                    st.error("❌ 帳號或密碼錯誤，請先註冊。")
                    
    elif auth_mode == "註冊新帳號":
        with st.form("register_form"):
            new_name = st.text_input("使用者名稱")
            new_email = st.text_input("Gmail (信箱)")
            new_pwd = st.text_input("密碼", type="password")
            confirm_pwd = st.text_input("確認密碼", type="password")
            submitted = st.form_submit_button("註冊", type="primary")
            
            if submitted:
                if new_email in db["users"]:
                    st.error("❌ 此信箱已經註冊過囉！")
                elif new_pwd != confirm_pwd:
                    st.error("❌ 兩次密碼輸入不一致！")
                elif not new_name or not new_email or not new_pwd:
                    st.error("❌ 欄位不可空白！")
                else:
                    is_student = False
                    school_abbr = ""
                    if ".edu.tw" in new_email:
                        is_student = True
                        try:
                            school_abbr = new_email.split('@')[1].split('.')[0]
                        except:
                            school_abbr = "Student"
                            
                    db["users"][new_email] = {
                        "name": new_name,
                        "pwd": new_pwd,
                        "is_student": is_student,
                        "school_abbr": school_abbr,
                        "credit_card": None,
                        "balance": 0,          # ✨ 創帳號時為 0 塊（防止洗錢）
                        "phone": None,         # ✨ 手機號碼紀錄
                        "phone_verified": False, # ✨ 手機驗證狀態
                        "remember_me": False,
                        "history": []
                    }
                    save_db(db)
                    st.success("✅ 註冊成功！帳戶餘額 NT$ 0。請登入後至左側綁定手機號碼領取 50 元獎勵金。")
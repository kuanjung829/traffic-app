import streamlit as st
from database import save_db

def render_auth_page(db):
    st.title("🚌 AI 智慧公車無感支付系統")
    auth_mode = st.radio("請選擇操作", ["登入", "註冊新帳號"], horizontal=True)
    
    if auth_mode == "登入":
        with st.form("login_form"):
            email = st.text_input("Gmail (帳號)")
            pwd = st.text_input("密碼", type="password")
            submitted = st.form_submit_button("登入", type="primary")
            if submitted:
                if email in db["users"] and db["users"][email]["pwd"] == pwd:
                    st.session_state.current_user = email
                    st.session_state.page = "dashboard"
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
                            
                    # 建立新會員資料
                    db["users"][new_email] = {
                        "name": new_name,
                        "pwd": new_pwd,
                        "is_student": is_student,
                        "school_abbr": school_abbr,
                        "credit_card": None,
                        "balance": 50, # ✨ 修改：註冊初始餘額改為 50 元
                        "history": []
                    }
                    save_db(db)
                    st.success("✅ 註冊成功！已獲得 NT$ 50 乘車金，請切換至「登入」頁面。")
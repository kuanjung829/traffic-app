# ui_sidebar.py
import streamlit as st
import re
import time
from database import save_db
from ui_face import render_face_verification  # 👈 匯入我們剛剛獨立出去的新模組

def render_sidebar(db, user_email):
    user_data = db["users"][user_email]
    
    if "balance" not in user_data:
        user_data["balance"] = 50
        save_db(db)
    if "remember_me" not in user_data:
        user_data["remember_me"] = False
        save_db(db)

    st.title("👤 會員專區")
    
    if user_data["is_student"]:
        st.markdown(f"### {user_data['school_abbr']} ({user_data['name']})")
        st.success("✅ 學生票優惠啟用")
    else:
        st.markdown(f"### {user_data['name']}")
        st.info("一般帳號 (無優惠)")
        
    st.divider()
    st.metric("💳 虛擬錢包餘額", f"NT$ {user_data['balance']}")
    
    st.divider()
    
    # 🤖 呼叫獨立的人臉識別模組
    render_face_verification(db, user_email)

    st.divider()
    st.markdown("### 🔒 支付與儲值管理")
    
    if not user_data["credit_card"]:
        st.warning("⚠️ 尚未綁定信用卡")
        with st.expander("💳 點擊展開：綁定信用卡"):
            cc_num = st.text_input("信用卡卡號 (16碼數字)", max_chars=16, key="cc_num")
            cc_date = st.text_input("有效期限 (MM/YY)", max_chars=5, key="cc_date")
            cc_cvv = st.text_input("安全碼 (3碼)", max_chars=3, type="password", key="cc_cvv")
            
            if st.button("確認綁定", type="primary", use_container_width=True):
                if not re.match(r"^\d{16}$", cc_num):
                    st.error("❌ 卡號格式錯誤！必須為 16 碼純數字。")
                elif not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", cc_date):
                    st.error("❌ 有效期限格式錯誤！請輸入 MM/YY。")
                elif not cc_cvv.isdigit() or len(cc_cvv) != 3:
                    st.error("❌ 安全碼格式錯誤！")
                else:
                    db["users"][user_email]["credit_card"] = cc_num
                    save_db(db)
                    st.success("✅ 信用卡綁定成功！")
                    time.sleep(1)
                    st.rerun()
    else:
        cc_hidden = f"**** **** **** {user_data['credit_card'][-4:]}"
        st.markdown(f"**已綁定信用卡**：`{cc_hidden}`")
        
        with st.expander("💰 儲值中心 (模擬)", expanded=False):
            add_amount = st.selectbox("選擇儲值金額", [15, 30, 50, 100, 300, 500])
            if st.button("確認儲值", use_container_width=True):
                db["users"][user_email]["balance"] += add_amount
                save_db(db)
                st.success(f"成功儲值 NT$ {add_amount}！")
                time.sleep(1)
                st.rerun()
        
        if st.button("❌ 解除綁定信用卡", use_container_width=True):
            db["users"][user_email]["credit_card"] = None
            save_db(db)
            st.rerun()
            
    st.divider()
    
    st.markdown("### 📜 歷史乘車紀錄")
    history_list = user_data.get("history", [])
    if not history_list:
        st.caption("尚無乘車紀錄")
    else:
        for idx, h in enumerate(reversed(history_list[-5:])):
            with st.expander(f"🚍 {h['route']} (-${h['fare']})"):
                st.caption(f"🕒 {h['time']}")
                st.write(f"**起點**: {h['start']}")
                st.write(f"**終點**: {h['end']}")
                st.write(f"**扣款金額**: NT$ {h['fare']}")
                st.success("✅ AI 無感支付完成")
                
    st.divider()
    
    if st.button("🚪 登出系統", use_container_width=True):
        if user_email in db["users"]:
            db["users"][user_email]["remember_me"] = False
            save_db(db)
            
        if "logged_in_user" in st.query_params:
            del st.query_params["logged_in_user"]
            
        st.session_state.current_user = None
        st.session_state.page = "login"
        st.rerun()
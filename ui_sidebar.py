import streamlit as st
import re
import time
from database import save_db

def render_sidebar(db, user_email):
    user_data = db["users"][user_email]
    
    # 確保舊帳號也有餘額欄位
    if "balance" not in user_data:
        user_data["balance"] = 50
        save_db(db)

    st.title("👤 會員專區")
    
    if user_data["is_student"]:
        st.markdown(f"### {user_data['school_abbr']} ({user_data['name']})")
        st.success("✅ 學生票優惠啟用")
    else:
        st.markdown(f"### {user_data['name']}")
        st.info("一般帳號 (無優惠)")
        
    st.divider()
    
    # 顯示餘額
    st.metric("💳 虛擬錢包餘額", f"NT$ {user_data['balance']}")
    
    st.divider()
    st.markdown("### 🔒 支付與儲值管理")
    
    # 邏輯判斷：尚未綁卡
    if not user_data["credit_card"]:
        st.warning("⚠️ 尚未綁定信用卡")
        
        # ✨ 優化：點擊展開才會出現輸入資料的表單
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
                
    # 邏輯判斷：已經綁卡
    else:
        cc_hidden = f"**** **** **** {user_data['credit_card'][-4:]}"
        st.markdown(f"**已綁定信用卡**：`{cc_hidden}`")
        
        # 儲值中心 (綁定後才顯示)
        with st.expander("💰 儲值中心 (模擬)", expanded=True):
            add_amount = st.selectbox("選擇儲值金額", [15, 30, 50, 100, 300, 500])
            if st.button("確認儲值", use_container_width=True):
                db["users"][user_email]["balance"] += add_amount
                save_db(db)
                st.success(f"成功儲值 NT$ {add_amount}！")
                time.sleep(1)
                st.rerun()
        
        # 解除綁定按鈕
        if st.button("❌ 解除綁定信用卡", use_container_width=True):
            db["users"][user_email]["credit_card"] = None
            save_db(db)
            st.rerun()
            
    st.divider()
    
    # 登出系統
    if st.button("🚪 登出系統", use_container_width=True):
        st.session_state.current_user = None
        st.session_state.page = "login"
        st.rerun()
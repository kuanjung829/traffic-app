import streamlit as st
import re
import time
from database import save_db

def render_payment_tab(db, user_email):
    user_data = db["users"][user_email]
    
    if user_data["credit_card"]:
        st.success("✅ 您已經綁定過信用卡了，無需重新綁定！(如需更換請至左側解除)")
    else:
        st.markdown("### 🔒 安全綁定支付信用卡")
        cc_num = st.text_input("信用卡卡號 (16碼數字)", max_chars=16)
        cc_date = st.text_input("有效期限 (MM/YY)", max_chars=5)
        cc_cvv = st.text_input("安全碼 (3碼)", max_chars=3, type="password")
        
        if st.button("確認綁定", type="primary"):
            if not re.match(r"^\d{16}$", cc_num):
                st.error("❌ 卡號格式錯誤！必須為 16 碼純數字。")
            elif not re.match(r"^(0[1-9]|1[0-2])\/\d{2}$", cc_date):
                st.error("❌ 有效期限格式錯誤！請輸入 MM/YY (例如 12/28)。")
            elif not cc_cvv.isdigit() or len(cc_cvv) != 3:
                st.error("❌ 安全碼格式錯誤！")
            else:
                db["users"][user_email]["credit_card"] = cc_num
                save_db(db)
                st.success("✅ 信用卡綁定成功！已永久寫入帳戶資料。")
                time.sleep(1)
                st.rerun()
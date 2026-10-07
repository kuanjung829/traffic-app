# ui_sidebar.py
import streamlit as st
import re
import time
import random
from database import save_db
from ui_face import render_face_verification

def render_sidebar(db, user_email):
    user_data = db["users"][user_email]
    
    # 初始化資料庫安全欄位
    if "balance" not in user_data:
        user_data["balance"] = 0
        save_db(db)
    if "remember_me" not in user_data:
        user_data["remember_me"] = False
        save_db(db)
    if "phone" not in user_data:
        user_data["phone"] = None
        save_db(db)
    if "phone_verified" not in user_data:
        user_data["phone_verified"] = False
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
    
    # ✨ 新增：手機號碼驗證與 50 元獎勵機制
    st.markdown("### 📱 手機號碼驗證 (領取50元)")
    if user_data["phone_verified"]:
        masked_phone = user_data["phone"][:4] + "****" + user_data["phone"][-2:]
        st.success(f"✅ 已綁定手機：`{masked_phone}`")
    else:
        st.warning("⚠️ 尚未綁定手機 (完成可獲 NT$ 50)")
        with st.expander("📱 點擊展開：綁定手機領取 50 元"):
            phone_input = st.text_input("手機號碼 (10碼，09開頭)", max_chars=10, key="phone_input")
            
            if "simulated_otp" not in st.session_state:
                st.session_state.simulated_otp = None
            
            if st.button("發送驗證碼", use_container_width=True):
                # 判定條件：10碼、前兩碼為 09
                if not re.match(r"^09\d{8}$", phone_input):
                    st.error("❌ 格式錯誤！必須為 10 碼純數字且以 09 開頭。")
                else:
                    # 隨機生成 6 位數驗證碼
                    st.session_state.simulated_otp = str(random.randint(100000, 999999))
                    st.success("驗證碼已發送！請查看下方模擬簡訊。")
            
            if st.session_state.simulated_otp:
                st.info(f"💬 【模擬簡訊】您的 6 位數驗證碼為：**{st.session_state.simulated_otp}**")
                code_input = st.text_input("輸入 6 位數驗證碼", max_chars=6, key="code_input")
                
                if st.button("確認驗證並獲得 50 元", type="primary", use_container_width=True):
                    if code_input == st.session_state.simulated_otp:
                        user_data["phone"] = phone_input
                        user_data["phone_verified"] = True
                        user_data["balance"] += 50  # 獲得 50 元獎勵
                        save_db(db)
                        st.session_state.simulated_otp = None
                        st.success("🎉 手機號碼綁定成功！已獲得 NT$ 50 註冊獎勵金！")
                        time.sleep(1.5)
                        st.rerun()
                    else:
                        st.error("❌ 驗證碼錯誤，請重新輸入！")

    st.divider()
    
    # 🤖 AI 人臉識別
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
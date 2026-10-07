# ui_face.py
import streamlit as st
import time
from database import save_db

def render_face_verification(db, user_email):
    user_data = db["users"][user_email]
    
    # 初始化資料庫中的人臉狀態
    if "face_verified" not in user_data:
        user_data["face_verified"] = False
        save_db(db)

    st.markdown("### 🤖 AI 人臉識別 (無感通行)")
    
    # 根據是否已驗證顯示不同介面
    if user_data["face_verified"]:
        st.success("✅ AI 人臉識別已驗證 (解鎖無感支付)")
        if st.button("🔄 重新進行人臉校正", use_container_width=True):
            user_data["face_verified"] = False
            save_db(db)
            st.rerun()
    else:
        st.warning("⚠️ 尚未進行 AI 人臉識別驗證")
        with st.expander("📷 點擊展開：AI 人臉建模與驗證"):
            st.caption("請將臉部對準鏡頭，依序完成多角度特徵擷取。")
            
            if st.button("🚀 開始人臉識別建模", type="primary", use_container_width=True):
                placeholder = st.empty()
                
                # 1. 正臉倒數
                for i in range(3, 0, -1):
                    placeholder.markdown(f"### 👀 請看著鏡頭 (正臉)...\n# ⏳ 倒數 {i} 秒")
                    time.sleep(1)
                
                # 2. 左臉倒數
                for i in range(3, 0, -1):
                    placeholder.markdown(f"### 👈 請慢慢轉向左臉...\n# ⏳ 倒數 {i} 秒")
                    time.sleep(1)
                    
                # 3. 右臉倒數
                for i in range(3, 0, -1):
                    placeholder.markdown(f"### 👉 請慢慢轉向右臉...\n# ⏳ 倒數 {i} 秒")
                    time.sleep(1)
                    
                placeholder.empty()
                user_data["face_verified"] = True
                save_db(db)
                st.success("🎉 AI 生物特徵建模成功！無感支付功能已解鎖。")
                time.sleep(1.5)
                st.rerun()
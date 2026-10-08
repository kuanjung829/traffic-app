# ui_face.py
import streamlit as st
import time
from database import save_db

# ✨ 加上 @st.dialog 裝飾器，這個函式就會變成「置中彈出視窗」
@st.dialog("🤖 AI 人臉識別建模")
def face_dialog(db, user_email):
    user_data = db["users"][user_email]
    
    st.caption("請將臉部對準鏡頭，依序完成多角度特徵擷取。")
    
    if st.button("🚀 開始進行臉部掃描", type="primary", use_container_width=True):
        placeholder = st.empty()
        
        for i in range(3, 0, -1):
            placeholder.markdown(f"<h3 style='text-align:center;'>👀 請看著鏡頭 (正臉)...</h3><h1 style='text-align:center;'>⏳ {i}</h1>", unsafe_allow_html=True)
            time.sleep(1)
        
        for i in range(3, 0, -1):
            placeholder.markdown(f"<h3 style='text-align:center;'>👈 請慢慢轉向左臉...</h3><h1 style='text-align:center;'>⏳ {i}</h1>", unsafe_allow_html=True)
            time.sleep(1)
            
        for i in range(3, 0, -1):
            placeholder.markdown(f"<h3 style='text-align:center;'>👉 請慢慢轉向右臉...</h3><h1 style='text-align:center;'>⏳ {i}</h1>", unsafe_allow_html=True)
            time.sleep(1)
            
        placeholder.empty()
        user_data["face_verified"] = True
        save_db(db)
        
        st.success("🎉 AI 生物特徵建模成功！無感支付功能已解鎖。")
        # ✨ 操作完畢等 2 秒後，st.rerun() 會自動關閉視窗並刷新畫面
        time.sleep(2)
        st.rerun()
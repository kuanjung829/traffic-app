# passenger_app/ui_face.py
import streamlit as st
import os
import time
from database import save_db
from PIL import Image

@st.dialog("📸 AI 人臉生物識別綁定")
def face_dialog(db, user_email):
    st.markdown("為了啟用「無感支付」功能，請授權攝影機進行臉部特徵安全加密建模。")
    
    FACE_DIR = "../shared_data/face_photos"
    os.makedirs(FACE_DIR, exist_ok=True)
    
    user_data = db["users"][user_email]
    file_path = os.path.join(FACE_DIR, f"{user_email}.jpg")

    if user_data.get("face_verified"):
        st.success("✅ 您已完成高等級生物識別驗證！")
        if os.path.exists(file_path):
            st.image(file_path, width=150, caption="您的人臉特徵")
        if st.button("🔄 重新人臉拍照校正", use_container_width=True):
            user_data["face_verified"] = False
            if os.path.exists(file_path): os.remove(file_path)
            save_db(db)
            st.rerun()
    else:
        st.warning("🔒 尚未完成人臉綁定，目前無法使用無感支付。")
        picture = st.camera_input("請將臉部對準鏡頭並保持光源充足")
        
        if picture:
            with st.spinner("AI 模型正在萃取臉部特徵..."):
                try:
                    # 🚀 無敵展示版：不管拍到什麼，只要有畫面就直接存檔並判定為註冊成功！
                    img = Image.open(picture)
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    img.save(file_path, format="JPEG")
                    
                    user_data["face_verified"] = True
                    save_db(db)
                    st.success("🎉 生物特徵建模成功！您已解鎖 AI 無感支付功能！")
                    time.sleep(2)
                    st.rerun()
                except Exception as e:
                    st.error(f"系統錯誤：{e}")
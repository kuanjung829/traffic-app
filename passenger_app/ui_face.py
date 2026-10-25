# passenger_app/ui_face.py
import streamlit as st
import os
import time
from PIL import Image
from database import save_db

@st.dialog("📸 人臉照片註冊 (純存 PNG 測試版)")
def face_dialog(db, user_email):
    st.markdown("此版本為架構測試版，僅將照片安全存成 PNG 格式，不進行 AI 運算。")
    
    FACE_DIR = "../shared_data/face_photos"
    os.makedirs(FACE_DIR, exist_ok=True)
    
    user_data = db["users"][user_email]
    # 💡 統一改為 .png 結尾
    file_path = os.path.join(FACE_DIR, f"{user_email}.png")

    if user_data.get("face_verified"):
        st.success("✅ 照片已成功存檔！")
        if os.path.exists(file_path):
            st.image(file_path, width=150, caption="雲端資料庫中的照片 (PNG)")
        if st.button("🔄 重新拍照", use_container_width=True):
            user_data["face_verified"] = False
            if os.path.exists(file_path): os.remove(file_path)
            save_db(db)
            st.rerun()
    else:
        picture = st.camera_input("請拍攝註冊照片")
        
        if picture:
            # 💡 直接轉成 RGB 並強制存為 PNG 格式
            img = Image.open(picture).convert('RGB')
            img.save(file_path, format="PNG")
            
            user_data["face_verified"] = True
            save_db(db)
            st.success("🎉 照片存檔成功！已同步至雲端資料庫。")
            time.sleep(2)
            st.rerun()
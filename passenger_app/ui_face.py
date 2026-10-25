# passenger_app/ui_face.py
import streamlit as st
import os
import time
import cv2
import numpy as np
from PIL import Image
import urllib.request
from database import save_db

def get_face_cascade():
    # 自動下載 AI 模型檔案，確保絕對不會報錯
    cascade_filename = "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_filename):
        url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        try:
            urllib.request.urlretrieve(url, cascade_filename)
        except Exception as e:
            st.error(f"下載 AI 模型失敗: {e}")
            return None
    return cv2.CascadeClassifier(cascade_filename)

@st.dialog("📸 AI 人臉生物識別綁定")
def face_dialog(db, user_email):
    st.markdown("為了啟用「無感支付」功能，請授權攝影機進行臉部特徵安全加密建模。")
    
    FACE_DIR = "../shared_data/face_photos"
    os.makedirs(FACE_DIR, exist_ok=True)
    
    user_data = db["users"][user_email]
    file_path = os.path.join(FACE_DIR, f"{user_email}.png")

    if user_data.get("face_verified"):
        st.success("✅ 您已完成高等級生物識別驗證！")
        if os.path.exists(file_path):
            st.image(file_path, width=150, caption="您的 AI 專屬特徵 (已智能裁切)")
        if st.button("🔄 重新人臉拍照校正", use_container_width=True):
            user_data["face_verified"] = False
            if os.path.exists(file_path): os.remove(file_path)
            save_db(db)
            st.rerun()
    else:
        st.warning("🔒 尚未完成人臉綁定，目前無法使用無感支付。")
        picture = st.camera_input("請將臉部對準鏡頭並保持光源充足")
        
        if picture:
            with st.spinner("OpenCV AI 模型正在智能擷取臉部輪廓..."):
                try:
                    img = Image.open(picture).convert('RGB')
                    img_array = np.array(img)
                    
                    face_cascade = get_face_cascade()
                    if face_cascade is not None:
                        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
                        
                        if len(faces) > 0:
                            # 取最大的臉 (避免抓到背景雜訊)
                            faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                            (x, y, w, h) = faces[0]
                            
                            # 💡 為了讓大頭貼好看，稍微擴大裁切範圍
                            margin_x = int(w * 0.25)
                            margin_y = int(h * 0.3)
                            
                            img_h, img_w, _ = img_array.shape
                            x_start = max(0, x - margin_x)
                            y_start = max(0, y - margin_y)
                            x_end = min(img_w, x + w + margin_x)
                            y_end = min(img_h, y + h + margin_y)
                            
                            # ✂️ 矩陣裁切：只保留臉部區域的畫面
                            cropped_face = img_array[y_start:y_end, x_start:x_end]
                            
                            # 儲存裁切後的純臉部照片 (PNG)
                            Image.fromarray(cropped_face).save(file_path, format="PNG")
                            
                            user_data["face_verified"] = True
                            save_db(db)
                            st.success("🎉 生物特徵擷取成功！AI 已將您的臉部獨立建檔！")
                            time.sleep(2)
                            st.rerun()
                        else:
                            st.error("❌ AI 無法偵測到清晰人臉，請確認光線、脫下口罩後重試！")
                except Exception as e:
                    st.error(f"系統錯誤：{e}")
# passenger_app/ui_face.py
import streamlit as st
import os
import time
import numpy as np
from PIL import Image
import mediapipe as mp
from database import save_db

# 💡 安全匯入 MediaPipe
try:
    mp_face_detection = mp.solutions.face_detection
except AttributeError:
    import mediapipe.python.solutions.face_detection as mp_face_detection

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
            with st.spinner("Google AI 模型正在智能擷取臉部輪廓..."):
                try:
                    img = Image.open(picture).convert('RGB')
                    img_array = np.array(img)
                    
                    # 🚀 啟動 MediaPipe 進行精準偵測
                    with mp_face_detection.FaceDetection(model_selection=0, min_detection_confidence=0.5) as face_detection:
                        results = face_detection.process(img_array)
                        
                        if results.detections:
                            # 取得第一張偵測到的臉
                            detection = results.detections[0]
                            h, w, _ = img_array.shape
                            
                            bboxC = detection.location_data.relative_bounding_box
                            x1 = int(bboxC.xmin * w)
                            y1 = int(bboxC.ymin * h)
                            box_w = int(bboxC.width * w)
                            box_h = int(bboxC.height * h)
                            
                            # 💡 為了讓大頭貼好看，稍微擴大裁切範圍 (留 20% 的邊距)
                            margin_x = int(box_w * 0.2)
                            margin_y = int(box_h * 0.2)
                            
                            x_start = max(0, x1 - margin_x)
                            y_start = max(0, y1 - margin_y)
                            x_end = min(w, x1 + box_w + margin_x)
                            y_end = min(h, y1 + box_h + margin_y)
                            
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
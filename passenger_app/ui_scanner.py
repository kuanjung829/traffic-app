# passenger_app/ui_scanner.py
import streamlit as st
import os
import json
import time
import cv2
import numpy as np
from PIL import Image
import urllib.request
from database import save_db

LOCAL_BUS_DB_PATH = "../shared_data/local_bus_transactions.json"
SCAN_DIR = "../shared_data/bus_scans"

def load_local_bus_db():
    if not os.path.exists(LOCAL_BUS_DB_PATH):
        return {"bus_id": "新竹客運-架構測試車", "total_revenue": 0, "transactions": []}
    with open(LOCAL_BUS_DB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def save_local_bus_db(data):
    with open(LOCAL_BUS_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_face_cascade():
    cascade_filename = "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_filename):
        url = "https://raw.githubusercontent.com/opencv/opencv/master/data/haarcascades/haarcascade_frontalface_default.xml"
        try:
            urllib.request.urlretrieve(url, cascade_filename)
        except Exception as e:
            st.error(f"下載 AI 模型失敗: {e}")
            return None
    return cv2.CascadeClassifier(cascade_filename)

def render_scanner(cloud_db):
    st.title("🚌 新竹客運 雙資料庫測試驗票機")
    st.caption("展示雲端與本機雙資料庫存檔架構 (含 AI 綠框視覺特效與智能裁切，沒臉不扣款版)")
    st.markdown("---")

    os.makedirs(SCAN_DIR, exist_ok=True)

    col_cam, col_info = st.columns([1.5, 1])

    with col_cam:
        st.subheader("📷 乘客上車掃描區")
        registered_users = [email for email, data in cloud_db["users"].items() if data.get("face_verified")]
        if not registered_users:
            st.warning("目前沒有任何已註冊照片的帳號，請先回乘客端註冊。")
            return
            
        simulated_user = st.selectbox("請選擇要模擬扣款的帳號 (代替 AI 辨識):", registered_users)
        picture = st.camera_input("請拍攝上車存證照片", key="bus_cam")

    with col_info:
        st.subheader("💳 交易狀態看板")
        status_placeholder = st.empty()
        
        local_db = load_local_bus_db()
        st.divider()
        st.metric("🚌 本機台今日累計營收", f"NT$ {local_db['total_revenue']}")

    # 建立大腦記憶防重複扣款
    if "last_processed_pic_size" not in st.session_state:
        st.session_state.last_processed_pic_size = None
    if "last_status_msg" not in st.session_state:
        st.session_state.last_status_msg = "等待乘客拍攝上車照片..."

    if picture and simulated_user:
        current_pic_size = len(picture.getvalue())
        
        img = Image.open(picture).convert('RGB')
        img_array = np.array(img)
        
        # 💡 準備兩張圖：一張用來畫綠框給畫面顯示，另一張用來裁切存檔
        display_img = img_array.copy()
        cropped_face = None 
        
        # ==========================================
        # 🤖 視覺特效：用 OpenCV 偵測、畫綠框並裁切
        # ==========================================
        face_detected = False
        face_cascade = get_face_cascade()
        
        if face_cascade is not None:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            
            if len(faces) > 0:
                face_detected = True
                # 取最大的臉 (避免抓到背景雜訊)
                faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                (x, y, w, h) = faces[0]
                
                # 1. 在顯示用的圖片上畫亮綠色方框
                cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 4)
                cv2.putText(display_img, "FACE TRACKED", (x, max(20, y - 10)), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # 2. 計算裁切範圍 (留白邊距，確保大頭貼完整)
                margin_x = int(w * 0.25)
                margin_y = int(h * 0.3)
                img_h, img_w, _ = img_array.shape
                
                x_start = max(0, x - margin_x)
                y_start = max(0, y - margin_y)
                x_end = min(img_w, x + w + margin_x)
                y_end = min(img_h, y + h + margin_y)
                
                # 3. ✂️ 從「沒有綠框的原始圖片」上，把臉部切下來準備存檔
                cropped_face = img_array[y_start:y_end, x_start:x_end]
                        
        with col_cam:
            if face_detected:
                st.image(display_img, caption="🟢 AI 已鎖定臉部特徵框", use_container_width=True)
            else:
                st.image(display_img, caption="⚠️ 未精準捕捉到完整正面五官，請正對鏡頭", use_container_width=True)
        # ==========================================

        if st.session_state.last_processed_pic_size != current_pic_size:
            if not face_detected:
                error_msg = "### 🔴 扣款失敗：未偵測到人臉！\n系統無法確認乘客身分，請確保臉部清晰並直視鏡頭後再試一次。"
                st.session_state.last_processed_pic_size = current_pic_size
                st.session_state.last_status_msg = error_msg
                status_placeholder.error(error_msg)
            else:
                # 執行存證與扣款
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                scan_filename = f"scan_{simulated_user}_{timestamp}.png"
                scan_path = os.path.join(SCAN_DIR, scan_filename)
                
                # 💡 存檔時，只存裁切下來的大頭貼，不再存入包含背景的全圖！
                Image.fromarray(cropped_face).save(scan_path, format="PNG")
                
                user_info = cloud_db["users"][simulated_user]
                base_fare = 15
                actual_fare = int(base_fare * 0.8) if user_info.get("is_student") else base_fare
                
                if user_info["balance"] >= actual_fare:
                    user_info["balance"] -= actual_fare
                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    
                    local_db["total_revenue"] += actual_fare
                    local_db["transactions"].append({
                        "passenger": simulated_user,
                        "fare": actual_fare,
                        "time": current_time,
                        "status": "success",
                        "scan_image": scan_filename
                    })
                    
                    save_db(cloud_db)
                    save_local_bus_db(local_db)
                    
                    success_msg = f"### 🟢 雙資料庫連線扣款成功！\n* **存證照片**：已智能裁切臉部特徵並存檔\n* **乘客身分**：{user_info['name']}\n* **扣款金額**：NT$ {actual_fare}\n* **剩餘餘額**：NT$ {user_info['balance']}"
                    
                    st.session_state.last_processed_pic_size = current_pic_size
                    st.session_state.last_status_msg = success_msg
                    status_placeholder.success(success_msg)
                else:
                    error_msg = f"### 🔴 扣款失敗：餘額不足！\n* **乘客身分**：{simulated_user}\n* **剩餘餘額**：NT$ {user_info['balance']} (需 NT$ {actual_fare})"
                    st.session_state.last_processed_pic_size = current_pic_size
                    st.session_state.last_status_msg = error_msg
                    status_placeholder.error(error_msg)
        else:
            if "成功" in st.session_state.last_status_msg:
                status_placeholder.success(st.session_state.last_status_msg)
            else:
                status_placeholder.error(st.session_state.last_status_msg)
    else:
        status_placeholder.info("等待乘客拍攝上車照片...")
        st.session_state.last_processed_pic_size = None
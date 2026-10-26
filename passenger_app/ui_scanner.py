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
        except Exception:
            return None
    return cv2.CascadeClassifier(cascade_filename)

def render_scanner(cloud_db):
    st.title("🚌 新竹客運 雙資料庫驗票機")
    st.caption("具備 AI 視覺裁切、訂單查驗與預先授權(凍結扣款)機制")
    st.markdown("---")

    os.makedirs(SCAN_DIR, exist_ok=True)
    col_cam, col_info = st.columns([1.5, 1])

    with col_cam:
        st.subheader("📷 乘客上車掃描區")
        registered_users = [email for email, data in cloud_db["users"].items() if data.get("face_verified")]
        if not registered_users:
            st.warning("目前沒有任何已註冊照片的帳號。")
            return
            
        simulated_user = st.selectbox("請選擇模擬刷臉的帳號:", registered_users)
        picture = st.camera_input("請拍攝上車存證照片", key="bus_cam")

    with col_info:
        st.subheader("💳 交易狀態看板")
        status_placeholder = st.empty()
        
        local_db = load_local_bus_db()
        st.divider()
        st.metric("🚌 本機台今日累計營收", f"NT$ {local_db['total_revenue']}")

    if "last_processed_pic_size" not in st.session_state:
        st.session_state.last_processed_pic_size = None
    if "last_status_msg" not in st.session_state:
        st.session_state.last_status_msg = "等待乘客上車刷臉..."

    if picture and simulated_user:
        current_pic_size = len(picture.getvalue())
        img = Image.open(picture).convert('RGB')
        img_array = np.array(img)
        display_img = img_array.copy()
        cropped_face = None 
        
        face_detected = False
        face_cascade = get_face_cascade()
        
        if face_cascade is not None:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            
            if len(faces) > 0:
                face_detected = True
                faces = sorted(faces, key=lambda x: x[2]*x[3], reverse=True)
                (x, y, w, h) = faces[0]
                
                cv2.rectangle(display_img, (x, y), (x + w, y + h), (0, 255, 0), 4)
                cv2.putText(display_img, "FACE TRACKED", (x, max(20, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                margin_x = int(w * 0.25)
                margin_y = int(h * 0.3)
                img_h, img_w, _ = img_array.shape
                x_start, y_start = max(0, x - margin_x), max(0, y - margin_y)
                x_end, y_end = min(img_w, x + w + margin_x), min(img_h, y + h + margin_y)
                
                cropped_face = img_array[y_start:y_end, x_start:x_end]
                        
        with col_cam:
            if face_detected:
                st.image(display_img, caption="🟢 AI 已鎖定臉部", use_container_width=True)
            else:
                st.image(display_img, caption="⚠️ 未捕捉到人臉", use_container_width=True)

        if st.session_state.last_processed_pic_size != current_pic_size:
            if not face_detected:
                error_msg = "### 🔴 拒絕登車：未偵測到人臉！\n請確保臉部清晰並直視鏡頭。"
                st.session_state.last_processed_pic_size = current_pic_size
                st.session_state.last_status_msg = error_msg
                status_placeholder.error(error_msg)
            else:
                user_info = cloud_db["users"][simulated_user]
                
                # 初始化防呆
                if "frozen_balance" not in user_info: user_info["frozen_balance"] = 0
                if "history" not in user_info: user_info["history"] = []
                
                # 🔍 核心防呆機制：檢查該帳號有沒有下訂單
                pending_orders = [o for o in user_info["history"] if o.get("status") == "pending"]
                
                if not pending_orders:
                    # ⛔ 沒下訂單，拒絕扣款
                    error_msg = f"### 🔴 拒絕登車：找不到預約訂單！\n乘客 **{user_info['name']}** 尚未在 APP 下單，無法扣款。\n請先預約路線後再上車刷臉。"
                    st.session_state.last_processed_pic_size = current_pic_size
                    st.session_state.last_status_msg = error_msg
                    status_placeholder.error(error_msg)
                else:
                    # ✅ 有訂單，抓取最前面第一筆進行正式扣款 (分段搭乘邏輯)
                    active_order = pending_orders[0]
                    actual_fare = active_order["fare"]
                    
                    if user_info["frozen_balance"] >= actual_fare:
                        # 將錢從凍結餘額中扣除 (代表這筆錢已經交給客運公司)
                        user_info["frozen_balance"] -= actual_fare
                        active_order["status"] = "completed"  # 標記為已搭乘
                        
                        # 儲存照片與日誌
                        timestamp = time.strftime("%Y%m%d_%H%M%S")
                        scan_filename = f"scan_{simulated_user}_{timestamp}.png"
                        scan_path = os.path.join(SCAN_DIR, scan_filename)
                        Image.fromarray(cropped_face).save(scan_path, format="PNG")
                        
                        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                        local_db["total_revenue"] += actual_fare
                        local_db["transactions"].append({
                            "passenger": simulated_user,
                            "route": active_order["route"],
                            "fare": actual_fare,
                            "time": current_time,
                            "status": "success",
                            "scan_image": scan_filename
                        })
                        
                        save_db(cloud_db)
                        save_local_bus_db(local_db)
                        
                        success_msg = f"### 🟢 驗票成功！\n**搭乘路線**：{active_order['route']}\n**乘客身分**：{user_info['name']}\n**正式扣款**：NT$ {actual_fare} (自凍結款項扣除)\n**可用餘額**：NT$ {user_info['balance']}"
                        
                        st.session_state.last_processed_pic_size = current_pic_size
                        st.session_state.last_status_msg = success_msg
                        status_placeholder.success(success_msg)
                    else:
                        error_msg = f"### 🔴 系統異常：凍結餘額不足扣款！"
                        st.session_state.last_processed_pic_size = current_pic_size
                        st.session_state.last_status_msg = error_msg
                        status_placeholder.error(error_msg)
        else:
            if "成功" in st.session_state.last_status_msg:
                status_placeholder.success(st.session_state.last_status_msg)
            else:
                status_placeholder.error(st.session_state.last_status_msg)
    else:
        status_placeholder.info("等待乘客上車刷臉...")
        st.session_state.last_processed_pic_size = None
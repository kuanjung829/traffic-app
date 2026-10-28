import streamlit as st
import os
import json
import time
import cv2
import numpy as np
from PIL import Image
import urllib.request
from database import save_db

# 🌟 引入強大的 DeepFace 深度學習套件
from deepface import DeepFace

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
    st.caption("具備 AI 視覺裁切、深度特徵比對與預先授權(凍結扣款)機制")
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
        
        st.divider()
        # 🌟 修改點 1：先預留一個空間，等下方 AI 算完、扣款完後，再把最新的營收寫進來
        revenue_placeholder = st.empty()

    # 預設待機畫面
    WAITING_HTML = """
        <div style='background-color:#1a1a1a; border: 2px dashed #555; padding: 50px 20px; border-radius: 12px; text-align:center;'>
            <h3 style='color:#777; font-family: "Courier New", Courier, monospace; letter-spacing: 3px; margin:0;'>WAITING...</h3>
            <div style='color:#555; margin-top:10px; font-size:15px;'>請乘客正對鏡頭進行刷臉</div>
        </div>
    """

    if "last_processed_pic_size" not in st.session_state:
        st.session_state.last_processed_pic_size = None
    if "last_status_msg" not in st.session_state:
        st.session_state.last_status_msg = WAITING_HTML

    local_db = load_local_bus_db()

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
                error_html = """
                    <div style='background-color:#1e1e1e; border: 3px solid #dc3545; padding: 25px; border-radius: 12px; box-shadow: inset 0 0 20px rgba(220, 53, 69, 0.3);'>
                        <h2 style='color:#ff4d4d; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>❌ 拒絕驗證</h2>
                        <hr style='border-color:#444; margin: 15px 0;'>
                        <p style='color:#ccc; font-size:18px; text-align:center; font-weight: bold;'>未偵測到人臉，請直視鏡頭</p>
                    </div>
                """
                st.session_state.last_processed_pic_size = current_pic_size
                st.session_state.last_status_msg = error_html
                status_placeholder.markdown(error_html, unsafe_allow_html=True)
            else:
                user_info = cloud_db["users"][simulated_user]
                reference_pic_path = f"../shared_data/face_photos/{simulated_user}.png"
                
                if not os.path.exists(reference_pic_path):
                    error_html = f"""
                        <div style='background-color:#1e1e1e; border: 3px solid #dc3545; padding: 25px; border-radius: 12px; box-shadow: inset 0 0 20px rgba(220, 53, 69, 0.3);'>
                            <h2 style='color:#ff4d4d; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>❌ 系統異常</h2>
                            <hr style='border-color:#444; margin: 15px 0;'>
                            <p style='color:#ccc; font-size:18px; text-align:center; font-weight: bold;'>找不到 {user_info.get('name', '該乘客')} 的基準照片</p>
                        </div>
                    """
                    st.session_state.last_processed_pic_size = current_pic_size
                    st.session_state.last_status_msg = error_html
                    status_placeholder.markdown(error_html, unsafe_allow_html=True)
                else:
                    is_match = False
                    
                    # 🌟 原汁原味的 DeepFace 深度特徵比對
                    with st.spinner("🤖 正在進行 DeepFace 深度人臉特徵比對..."):
                        try:
                            result = DeepFace.verify(
                                img1_path = img_array, 
                                img2_path = reference_pic_path,
                                enforce_detection = False
                            )
                            is_match = result.get("verified", False)
                        except Exception as e:
                            st.error(f"AI 比對過程發生異常: {e}")
                            is_match = False

                    if not is_match:
                        error_html = f"""
                            <div style='background-color:#1e1e1e; border: 3px solid #dc3545; padding: 25px; border-radius: 12px; box-shadow: inset 0 0 20px rgba(220, 53, 69, 0.3);'>
                                <h2 style='color:#ff4d4d; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>❌ 拒絕登車</h2>
                                <hr style='border-color:#444; margin: 15px 0;'>
                                <p style='color:#ccc; font-size:18px; text-align:center; font-weight: bold;'>非本人！防盜刷機制已啟動</p>
                            </div>
                        """
                        st.session_state.last_processed_pic_size = current_pic_size
                        st.session_state.last_status_msg = error_html
                        status_placeholder.markdown(error_html, unsafe_allow_html=True)
                    else:
                        if "frozen_balance" not in user_info: user_info["frozen_balance"] = 0
                        if "history" not in user_info: user_info["history"] = []
                        
                        pending_orders = [o for o in user_info["history"] if o.get("status") == "pending"]
                        
                        if not pending_orders:
                            error_html = """
                                <div style='background-color:#1e1e1e; border: 3px solid #dc3545; padding: 25px; border-radius: 12px; box-shadow: inset 0 0 20px rgba(220, 53, 69, 0.3);'>
                                    <h2 style='color:#ff4d4d; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>❌ 拒絕登車</h2>
                                    <hr style='border-color:#444; margin: 15px 0;'>
                                    <p style='color:#ccc; font-size:18px; text-align:center; font-weight: bold;'>找不到預約訂單，請先下單</p>
                                </div>
                            """
                            st.session_state.last_processed_pic_size = current_pic_size
                            st.session_state.last_status_msg = error_html
                            status_placeholder.markdown(error_html, unsafe_allow_html=True)
                        else:
                            active_order = pending_orders[0]
                            actual_fare = active_order["fare"]
                            
                            if user_info["frozen_balance"] >= actual_fare:
                                user_info["frozen_balance"] -= actual_fare
                                active_order["status"] = "completed" 
                                
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
                                
                                st.toast("嗶！刷卡成功", icon="✅")
                                
                                # 🌟 修改點 2：高對比數位 POS 看板設計
                                success_html = f"""
                                    <div style='background-color:#0a1910; border: 3px solid #28a745; padding: 20px; border-radius: 12px; box-shadow: inset 0 0 25px rgba(40, 167, 69, 0.2);'>
                                        <h2 style='color:#39ff14; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>🟢 驗證與扣款成功</h2>
                                        <hr style='border-color:#194025; margin: 15px 0;'>
                                        <div style='color:#81c784; font-size: 15px; margin-bottom: 5px;'>👤 身分比對：相符 ({user_info.get('name', '')})</div>
                                        <div style='color:#81c784; font-size: 15px; margin-bottom: 15px;'>🚌 路線：{active_order['route']}</div>
                                        
                                        <div style='background-color:#050d08; padding: 15px; border-radius: 8px; border: 1px solid #194025;'>
                                            <div style='color:#6c757d; font-size: 13px; text-transform: uppercase;'>Deducted (自凍結扣除)</div>
                                            <div style='color:#39ff14; font-size: 38px; font-weight: bold; font-family: "Courier New", Courier, monospace;'>- NT$ {actual_fare}</div>
                                        </div>
                                        
                                        <div style='margin-top: 15px; color:#a5d6a7; font-size: 18px; text-align: right; font-weight: bold;'>
                                            剩餘可用餘額：NT$ {user_info['balance']}
                                        </div>
                                    </div>
                                """
                                
                                st.session_state.last_processed_pic_size = current_pic_size
                                st.session_state.last_status_msg = success_html
                                status_placeholder.markdown(success_html, unsafe_allow_html=True)
                            else:
                                error_html = """
                                    <div style='background-color:#1e1e1e; border: 3px solid #dc3545; padding: 25px; border-radius: 12px; box-shadow: inset 0 0 20px rgba(220, 53, 69, 0.3);'>
                                        <h2 style='color:#ff4d4d; text-align:center; margin:0; font-family: "Courier New", Courier, monospace; letter-spacing: 2px;'>❌ 餘額異常</h2>
                                        <hr style='border-color:#444; margin: 15px 0;'>
                                        <p style='color:#ccc; font-size:18px; text-align:center; font-weight: bold;'>凍結餘額不足扣款</p>
                                    </div>
                                """
                                st.session_state.last_processed_pic_size = current_pic_size
                                st.session_state.last_status_msg = error_html
                                status_placeholder.markdown(error_html, unsafe_allow_html=True)
    else:
        status_placeholder.markdown(st.session_state.last_status_msg, unsafe_allow_html=True)
        st.session_state.last_processed_pic_size = None

    # 🌟 修改點 3：將今日營收 metric 移到最後面渲染，確保拿到的是「剛剛扣款完」的最新數字
    revenue_placeholder.metric("🧾 本機台今日累計營收", f"NT$ {local_db['total_revenue']}")
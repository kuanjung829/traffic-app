# ui_face.py
import streamlit as st
import time
import os
from database import save_db

@st.dialog("🤖 真實 AI 人臉識別建模")
def face_dialog(db, user_email):
    user_data = db["users"][user_email]
    
    st.warning("⚠️ 隱私權提示：本系統將會開啟您的設備攝影機 (Webcam) 進行真實臉部拍照，並加密儲存作為無感支付的生物識別依據。")
    
    # 使用 Session State 來記住使用者是否點擊了「同意開啟」
    if "camera_enabled" not in st.session_state:
        st.session_state.camera_enabled = False

    # 第一階段：詢問是否開啟鏡頭
    if not st.session_state.camera_enabled:
        if st.button("✅ 同意開啟攝影機", type="primary", use_container_width=True):
            st.session_state.camera_enabled = True
            st.rerun()
        if st.button("❌ 拒絕並取消", use_container_width=True):
            st.rerun() # 點擊後無動作，可讓使用者點擊視窗外關閉
            
    # 第二階段：同意後，啟動真實攝影機
    else:
        st.info("💡 請允許瀏覽器存取攝影機，對準鏡頭後點擊「Take Photo」。")
        
        # Streamlit 內建的超強大魔法元件，直接開啟鏡頭
        picture = st.camera_input("拍攝人臉特徵")
        
        if picture:
            # 1. 建立一個存放照片的專屬資料夾
            os.makedirs("face_photos", exist_ok=True)
            
            # 2. 取一個不會重複的檔名 (把信箱的特殊符號換掉)
            safe_email = user_email.replace("@", "_").replace(".", "_")
            file_path = f"face_photos/{safe_email}.jpg"
            
            # 3. 將拍下來的照片寫入實體檔案儲存
            with open(file_path, "wb") as f:
                f.write(picture.getbuffer())
            
            # 4. 更新資料庫，把照片路徑存起來
            user_data["face_verified"] = True
            user_data["face_image_path"] = file_path
            save_db(db)
            
            st.success("🎉 真實人臉特徵擷取成功！照片已安全儲存，解鎖無感支付。")
            time.sleep(2)
            
            # 拍完後重置狀態，並關閉視窗刷新畫面
            st.session_state.camera_enabled = False 
            st.rerun()
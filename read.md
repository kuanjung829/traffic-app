# 🚌 AI 智慧公車無感支付系統 (AI Smart Bus Seamless Payment)

![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white)
![DeepFace](https://img.shields.io/badge/AI_DeepFace-000000?style=for-the-badge)
![Google Maps API](https://img.shields.io/badge/Google_Maps_API-4285F4?style=for-the-badge&logo=googlemaps&logoColor=white)

這是一款結合**深度學習人臉辨識**、**動態路線規劃**與**金融級虛擬錢包**的次世代大眾運輸解決方案。本系統將傳統的「投幣/刷卡」乘車體驗，升級為「先預約凍結、上車刷臉即走」的無感支付模式，並配備完整的商業防呆邏輯與司機端雙資料庫 POS 機。

---

## ✨ 核心特色功能

### 👤 生物辨識與無感支付 (Biometric & Seamless Payment)
* **AI 臉部建檔與追蹤**：使用 OpenCV (Haarcascade) 進行即時臉部追蹤與視覺裁切。
* **高精度防盜刷比對**：導入 DeepFace 深度神經網路，進行嚴格的特徵值比對，確保為本人搭乘。
* **金融級錢包系統**：具備嚴格正則表達式 (Regex) 的信用卡綁定與解綁功能、模擬簡訊驗證，以及乘車金儲值系統。

### 🗺️ 智慧路線規劃與防呆預約 (Smart Routing & Booking)
* **雙 API 智能導航**：整合 Google Maps Directions API 與台灣 TDX 運輸資料流通服務，提供精準轉乘路線與即時到站狀態。
* **逆向時間推算**：支援設定「希望抵達時間」，系統會自動反推最晚出發時間，並進行時間衝突攔截。
* **商業級防佔位機制**：預約成功後進行**車資預先凍結**，並啟動高質感**動態倒數計時器**。公車發車超過「1 分鐘靠站寬限期」未上車刷臉者，系統將自動沒收違約金。

### 🚌 雙資料庫驗票機系統 (Dual-DB POS Scanner)
* **高對比數位電子看板**：司機端配備高鐵/商用級別的黑綠底數位 POS 看板，提供視覺震撼的扣款回饋。
* **雲端與本地端雙軌架構**：模擬真實公車離線營運情境，具備 local_bus_transactions.json，精準紀錄單機今日累計營收與交易日誌。

### 📱 原生 APP 級 UI/UX (App-level UI)
* 全面隱藏 Streamlit 預設框架痕跡，打造沉浸式手機 App 體驗。
* 導入 st.toast 輕量化推播提示、並排響應式表單、電子車票卡片設計。
* 客製化地圖標記 ( 🟢起點 ➔ 🔵轉乘/途經 ➔ 🔴終點 )，路線導覽一目了然。

---

## 🛠️ 技術架構 (Tech Stack)

* **前端介面**：[Streamlit](https://streamlit.io/) + Custom HTML/CSS/JS (Components)
* **後端邏輯**：Python 3.11
* **AI 視覺**：OpenCV (haarcascade_frontalface_default.xml), DeepFace
* **API 串接**：Google Maps API (Transit Mode), MOTC TDX API
* **資料庫**：JSON (模擬關聯式資料庫與本地端資料同步)
* **狀態管理**：streamlit_cookies_controller (幽靈帳號防禦機制), st.session_state

---

## 🚀 安裝與執行指引

### 1. 複製專案與安裝依賴套件

git clone [https://github.com/你的帳號/你的專案庫名稱.git](https://github.com/你的帳號/你的專案庫名稱.git)
cd 你的專案庫名稱
pip install -r requirements.txt


### 2. 環境變數設定
請在專案根目錄或 Streamlit Secrets 中設定相關 API 金鑰：
* Google Maps API Key
* TDX Client ID & Client Secret
* (若佈署於雲端) 確保系統時區設定為 Asia/Taipei

### 3. 啟動應用程式
請進入主程式所在目錄，執行以下指令：

cd passenger_app
streamlit run app.py


---

## 📂 專案目錄結構

📦 project-root
 ┣ 📂 passenger_app       # 主應用程式資料夾
 ┃ ┣ 📜 app.py            # 系統進入點 (包含全域 CSS 優化與時區設定)
 ┃ ┣ 📜 ui_auth.py        # 登入與註冊介面
 ┃ ┣ 📜 ui_navigation.py  # 智慧路線查詢、電子車票、倒數防呆機制
 ┃ ┣ 📜 ui_sidebar.py     # 會員中心、信用卡綁定、錢包儲值
 ┃ ┣ 📜 ui_scanner.py     # 司機端驗票機 (DeepFace 驗證與數位 POS 看板)
 ┃ ┣ 📜 ui_face.py        # 人臉建檔與特徵儲存
 ┃ ┣ 📜 api_services.py   # Google Maps 與 TDX API 串接邏輯
 ┃ ┗ 📜 database.py       # 雲端資料庫讀寫模組
 ┣ 📂 shared_data         # 共享資料庫與圖片儲存區
 ┃ ┣ 📂 face_photos       # 乘客註冊之人臉特徵圖片
 ┃ ┣ 📂 bus_scans         # 乘車時實際刷臉之存證照片
 ┃ ┣ 📜 users_db.json     # 全域雲端會員資料庫
 ┃ ┗ 📜 local_bus_transactions.json # 驗票機本地端交易日誌與營收
 ┣ 📜 requirements.txt    # Python 依賴套件清單
 ┗ 📜 README.md           # 專案說明文件
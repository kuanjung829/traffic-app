🚌 AI 智慧公車與路線導航系統 (Smart Bus Payment & Transit Navigation System)

這是一套結合 AI 電腦視覺（臉部識別）、無感支付扣款、全台大眾運輸動態導航 以及 智慧時間段規劃 的現代化智慧交通與票證整合平台。本專案旨在提供如乘車碼、Apple Pay 般的流暢體驗，並透過直覺的 Web 介面實現完整的公共運輸數位轉型。

🌟 核心功能亮點 (Key Features)

1. 🤖 AI 臉部識別與雙解鎖無感支付

Webcam 硬體直連：利用 Streamlit 內建高畫質相機硬體串流即時捕捉使用者面部特徵。

生物特徵建模：拍攝照片後自動持久化儲存至本地 /face_photos/ 資料夾，完成無感支付驗證解鎖。

雙重驗證扣款 Gating：必須同時具備「足夠的錢包餘額」與「完成 AI 人臉識別」，才能啟動一鍵智慧扣款。

2. 💳 智慧會員中心與金融交易機制

手機驗證獎勵：輸入 10 碼手機號碼並通過 6 位數模擬簡訊 OTP 驗證，即可立即獲得 NT$ 50 迎賓獎勵金。

信用卡綁定與虛擬錢包：支援 16 碼信用卡驗證綁定與多面額虛擬錢包即時儲值（NT$ 15 ~ NT$ 500）。

3 分鐘發車退款緩衝期：購票後 3 分鐘內可於歷史乘車明細隨時「申請退款」，金額即時回補錢包；超過 3 分鐘發車後自動鎖定反灰，完美還原真實客運退票邏輯。

3. 🗺️ 智能路線與雙模式時間段規劃

⚡ 即時查詢模式：無需繁瑣設定，一鍵自動以當下系統時間向 Google Maps 查詢最快轉乘方案與即時公車動態。

🕒 特定查詢模式：支援「同時設定預計出發時間與希望抵達時間」，系統自動為使用者配對最完美、最貼切的班次。

自動化步行與轉乘拆解：清晰呈現步行距離、公車路線名稱、預計發車時間與剩餘停靠站數。

4. 🎓 學生專屬優惠折扣

學籍信箱識別：透過 .edu.tw 學校信箱註冊，系統自動判定並解鎖 全台公車票價 8 折優惠。

🏗️ 專案架構與模組說明 (Project Architecture)

本專案採用高度模組化設計，徹底解耦前端 UI 渲染、後端商業邏輯與外部 API 溝通：

traffic-app/
│
├── app.py                  # 主程式進入點、全局 CSS 美化與頁面路由器
├── database.py             # 本地 JSON 資料庫讀寫、會員持久化與交易紀錄管理
├── api_services.py         # 串接 Google Maps Directions API 與 TDX 官方公車即時動態
├── ui_auth.py              # 用戶登入、註冊與學生身份驗證介面
├── ui_sidebar.py           # 側邊欄會員中心、錢包儲值、手機/信用卡綁定、歷史明細彈窗
├── ui_face.py              # AI webcam 人臉拍照擷取與生物識別建模模組
├── ui_navigation.py        # 起迄點導航、時間段設定與即時/特定查詢介面
├── requirements.txt        # 專案 Python 依賴套件清單
├── .streamlit/
│   └── secrets.toml        # 機密金鑰與 API Token 本地設定檔
└── face_photos/            # 儲存用戶人臉識別截圖之資料夾


🚀 安裝與部署指南 (Installation & Deployment)

1. 環境需求

Python 3.10 或以上版本

穩定的網路連線（用於呼叫 Google Maps API 與中華民國交通部 TDX 運輸資料流通服務）

2. 下載與安裝依賴項目

在終端機執行以下指令安裝所需套件：

git clone https://github.com/kuanjung829/traffic-app.git
cd traffic-app
pip install -r requirements.txt


3. 設定環境金鑰 (Secrets Management)

於專案根目錄建立 .streamlit/secrets.toml 檔案，填入你的 Google Maps 與 TDX API 金鑰：

TDX_CLIENT_ID = "你的TDX_Client_ID"
TDX_CLIENT_SECRET = "你的TDX_Client_SECRET"
GOOGLE_MAPS_API_KEY = "你的Google_Maps_API_Key"


(若部署至 Streamlit Community Cloud，請直接至 App Dashboard 的 Settings -> Secrets 貼上以上 TOML 格式設定。)

4. 啟動應用程式

streamlit run app.py
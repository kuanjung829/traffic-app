# 🚌 AI 智慧公車無感支付系統 (Smart Bus Face-Pay System)

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Framework-FF4B4B.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer_Vision-5C3EE8.svg)
![Architecture](https://img.shields.io/badge/Architecture-Cloud--Edge_Split-brightgreen.svg)

本專案為一個基於 Python 與 Streamlit 開發的「公車人臉辨識扣款模擬系統」。透過整合 OpenCV 電腦視覺技術與雙資料庫（雲端/邊緣）架構，旨在解決傳統電子票證需實體刷卡、容易遺失或忘記帶卡的痛點，打造「上車即走、無感支付」的未來智慧交通體驗。

---

## 💡 開發動機與背景 (Background & Motivation)

在智慧城市推動下，大眾運輸工具的支付方式不斷革新。然而，現行的票卡或 QR Code 支付仍需要實體媒介與手動操作，在尖峰時段容易造成車門壅塞。
本專案發想自「無感支付」概念，以 AI 人臉辨識作為身分載體，探索將生物辨識技術導入日常交通系統的適配性與潛力。同時，為了克服公車行進間網路不穩定的真實場景，特別設計了 **Cloud-Edge 邊緣運算分離架構**。

---

## ✨ 核心架構 (Core Architecture)

系統完全模擬真實世界的公車運作環境，採用「雙資料庫」非同步設計，降低對雲端即時連線的依賴：

*   ☁️ **雲端資料庫 (`users_db.json`)**：
    *   模擬集中式伺服器，負責儲存乘客個資、虛擬錢包餘額、交易明細。
    *   管理並儲存高解析度的 AI 生物特徵大頭貼 (`face_photos`)。
*   🚌 **邊緣驗票機資料庫 (`local_bus_transactions.json`)**：
    *   模擬公車車機 (Edge Device) 的本端儲存。
    *   專門紀錄單機累計營收、上車存證照片 (`bus_scans`)，以及即時扣款日誌。

---

## 🚀 系統特色與功能 (Key Features)

### 👤 乘客端 (Passenger Web App)
*   **AI 智能生物建檔**：串接 OpenCV Haar Cascade 模型，自動偵測人臉輪廓並「智能裁切 (Smart Crop)」出乾淨的五官特徵，過濾多餘背景，建立標準化大頭貼資料庫。
*   **虛擬錢包與雙重驗證**：實作模擬簡訊 (OTP) 手機綁定與信用卡儲值功能，並具備學生票自動辨識與票價打折邏輯。
*   **動態乘車紀錄與退款防呆**：提供歷史搭乘明細查詢，並內建「3 分鐘內發車前防誤扣退款」的安全機制。
*   **Session 狀態持久化**：實作「保持登入」功能，確保跨頁面與重整時的使用者體驗。

### 💳 實體驗票機端 (Bus Scanner Edge)
*   **動態綠框視覺追蹤**：乘客上車時，系統會即時進行臉部捕捉，並在畫面上渲染追蹤綠框 (Face Tracked)，提供即時科技視覺回饋。
*   **智能裁切存證**：系統不會儲存包含雜亂背景的全螢幕畫面，而是精準裁切綠框內的臉部特徵作為交易存證。
*   **防重複扣款演算法 (Anti-Double Charge)**：利用 Session State 與影像位元組指紋 (Byte size) 進行比對，成功解決 Web 應用程式常見的「重整無限迴圈扣款」漏洞。
*   **無臉拒絕交易機制 (Face Gating)**：嚴格的閘道控制，若 AI 未偵測到完整人臉特徵，驗票機將自動攔截並拒絕扣款，防止誤觸。

---

## 📁 專案目錄結構 (Directory Structure)

```text
traffic-app/
├── passenger_app/                  # 主程式邏輯與 UI 介面區
│   ├── app.py                      # 系統主入口 (路由與初始化)
│   ├── database.py                 # 資料庫讀寫模組
│   ├── ui_auth.py                  # 登入與註冊介面
│   ├── ui_face.py                  # 乘客端 AI 生物建檔與智能裁切
│   ├── ui_scanner.py               # 公車驗票機端核心邏輯與視覺追蹤
│   └── ui_sidebar.py               # 側邊欄與會員中心控制
├── shared_data/                    # 雙資料庫與影像儲存區
│   ├── users_db.json               # ☁️ 雲端使用者資料庫
│   ├── local_bus_transactions.json # 🚌 邊緣車機交易日誌
│   ├── face_photos/                # 雲端乘客註冊大頭貼
│   └── bus_scans/                  # 車機端上車存證照片
└── requirements.txt                # 專案套件依賴清單
```

---

## 🛠️ 技術堆疊 (Tech Stack)

*   **Frontend & Web Framework**: Streamlit (快速建構資料應用 UI、Session 狀態管理)
*   **Computer Vision**: OpenCV (Haar Cascade 臉部特徵定位、綠框渲染、即時影像處理)
*   **Image Processing**: Pillow (PIL), NumPy (矩陣運算與智慧裁切)
*   **Database Engine**: JSON (實作輕量級 NoSQL 文件資料庫存取)

---

## 💻 快速啟動指南 (Quick Start)

1. **複製專案到本機**
```bash
git clone [https://github.com/kuanjung829/traffic-app.git](https://github.com/kuanjung829/traffic-app.git)
cd traffic-app/passenger_app
```

2. **安裝所需依賴套件**
```bash
pip install -r requirements.txt
```

3. **啟動系統**
```bash
cd passenger_app
python -m streamlit run app.py --server.port 8501
```
*(啟動後系統將自動於背景下載所需的 OpenCV 模型，並開啟瀏覽器進入系統)*

---

## 📓 開發者筆記：技術克服 (Developer Notes)

本系統在開發過程中，為解決複雜的 C++ 視覺引擎 (如 `dlib`, `face_recognition`, `MediaPipe`) 與 Streamlit 網頁單執行緒重繪機制衝突導致的崩潰問題，特別實作了**「系統解耦 (Decoupling)」**架構。

我們將容易報錯的底層 AI 比對引擎從前端資料流中獨立出來，改為「先由 OpenCV 輕量模型進行視覺追蹤與智能裁切，確保交易存檔穩定，後續再交由後台進行身分比對」的非同步概念架構。這大幅提升了系統在 Windows 環境下的穩定度與執行流暢性，展現了務實的軟體工程妥協與優化能力。

---

## 🎯 未來展望 (Future Roadmap)

*   [ ] **深度學習整合**：從 Haar Cascade 升級至更精確的 CNN/FaceNet 模型，實作真正的 1:N 人臉相似度比對扣款。
*   [ ] **資料庫雲端化**：將本地 JSON 資料庫遷移至 Firebase 或 MongoDB，實作跨裝置真正的雲端同步。
*   [ ] **即時路況 API 串接**：整合 TDX (運輸資料流通服務) API，於乘客端提供即時公車動態與到站時間預估。
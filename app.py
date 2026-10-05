import json
import time
import streamlit as st

# --- 1. 後端邏輯核心 (模組二與模組三) ---
def extract_destination(user_input: str) -> str:
    """模擬 AI 意圖與目的地萃取"""
    if "新竹火車站" in user_input:
        return "新竹火車站"
    elif "磐石高中" in user_input:
        return "磐石高中"
    elif "巨城購物中心" in user_input:
        return "巨城購物中心"
    else:
        return "未知地點"

def find_bus_routes(destination: str) -> dict:
    """模擬交通 API 路線規劃"""
    mock_routes_db = {
        "新竹火車站": [
            {
                "option_id": 1,
                "bus_route_name": "藍15區",
                "boarding_stop": "磐石高中",
                "alighting_stop": "新竹火車站",
                "estimated_wait_time_mins": 5,
                "travel_time_mins": 15,
                "fare": 15
            },
            {
                "option_id": 2,
                "bus_route_name": "23路",
                "boarding_stop": "中正市場",
                "alighting_stop": "火車站",
                "estimated_wait_time_mins": 8,
                "travel_time_mins": 18,
                "fare": 15
            }
        ],
        "巨城購物中心": [
            {
                "option_id": 1,
                "bus_route_name": "51路",
                "boarding_stop": "磐石高中",
                "alighting_stop": "巨城購物中心",
                "estimated_wait_time_mins": 6,
                "travel_time_mins": 12,
                "fare": 15
            }
        ]
    }
    routes = mock_routes_db.get(destination, [])
    if routes:
        return {"status": "success", "route_options": routes}
    else:
        return {"status": "not_found", "message": "查無直達公車路線"}

# --- 2. 前端介面設計 (Streamlit UI) ---
st.set_page_config(page_title="AI 智慧公車無感支付與導航", page_icon="🚌", layout="centered")

st.title("🚌 AI 智慧公車無感支付與動態導航")
st.write("輸入你想去的地方，體驗「開口即出發、走過即扣款」的零延遲乘車體驗！")

# 初始化 Session State 追蹤狀態
if "step" not in st.session_state:
    st.session_state.step = "search"
if "selected_route" not in st.session_state:
    st.session_state.selected_route = None

# 使用者輸入區
user_input = st.text_input("你想去哪裡？", placeholder="例如：我現在要去新竹火車站")

if st.button("🚀 開始 AI 導航查詢", type="primary"):
    if user_input:
        st.session_state.destination = extract_destination(user_input)
        st.session_state.route_result = find_bus_routes(st.session_state.destination)
        st.session_state.step = "search_done"
    else:
        st.error("⚠️ 請先在上方輸入您的目的地或需求！")

# 如果已經完成查詢，且尚未進入支付模擬
if "destination" in st.session_state and st.session_state.step in ["search_done", "search"]:
    destination = st.session_state.destination
    route_result = st.session_state.route_result
    
    st.success(f"✅ AI 成功解析目的地：**{destination}**")
    
    if route_result["status"] == "success":
        st.subheader("💡 推薦搭乘路線")
        for opt in route_result["route_options"]:
            with st.container(border=True):
                st.markdown(f"### 🚍 建議搭乘：{opt['bus_route_name']}")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("預估等候", f"{opt['estimated_wait_time_mins']} 分鐘")
                with col2:
                    st.metric("預估車程", f"{opt['travel_time_mins']} 分鐘")
                with col3:
                    st.metric("乘車票價", f"${opt['fare']} 元")
                
                st.text(f"📍 上車站牌：{opt['boarding_stop']} ➔ 下車站牌：{opt['alighting_stop']}")
                
                # 點擊後進入無感支付模擬流程
                if st.button(f"確認搭乘此班次 ({opt['bus_route_name']})", key=opt['option_id']):
                    st.session_state.selected_route = opt
                    st.session_state.step = "payment_simulation"
                    st.rerun()
    else:
        st.warning(route_result["message"])

# --- 3. 無感支付與車載 AI 感應模擬狀態 ---
if st.session_state.step == "payment_simulation":
    opt = st.session_state.selected_route
    st.markdown("---")
    st.subheader("🔄 車載 Edge AI 感應與無感支付進行中...")
    
    # 動態進度模擬
    with st.status("正在與車載系統建立連線...", expanded=True) as status:
        st.write("📡 階段 1/3：已向後端寫入待扣款狀態 (`Ready to Board`)")
        time.sleep(0.8)
        st.write(f"🚌 階段 2/3：車載 AI 鏡頭與手機藍牙訊號比對中 (班次: {opt['bus_route_name']})...")
        time.sleep(1.0)
        st.write("✨ 階段 3/3：身分特徵匹配成功！正在自動觸發電子支付...")
        time.sleep(0.8)
        status.update(label="🎉 無感支付與乘車綁定成功！", state="complete", expanded=False)
    
    st.balloons()
    
    # 顯示數位乘車憑證與交易收據
    with st.container(border=True):
        st.markdown("### 💳 數位乘車憑證與交易收據")
        st.markdown(f"- **搭乘班次**：`{opt['bus_route_name']}`")
        st.markdown(f"- **乘車區間**：{opt['boarding_stop']} ➔ {opt['alighting_stop']}")
        st.markdown(f"- **扣款金額**：**NT$ {opt['fare']} 元**")
        st.markdown(f"- **支付狀態**：<span style='color:green;'>**已自動扣款 (無感支付完成)**</span>", unsafe_allow_html=True)
        st.markdown(f"- **帳戶剩餘餘額**：NT$ 385 元")
    
    st.info("💡 提示：您已可直接上車找位子坐，無需刷任何卡片或條碼！")
    
    if st.button("🔄 重新進行下一趟查詢"):
        st.session_state.step = "search"
        st.session_state.selected_route = None
        st.rerun()
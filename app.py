import json
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
st.set_page_config(page_title="AI 智慧公車導航助理", page_icon="🚌", layout="centered")

st.title("🚌 AI 智慧公車無感支付與動態導航")
st.write("輸入你想去的地方，讓 AI 助理為你瞬間規劃最佳公車路線，開啟無感乘車體驗！")

# 建立文字輸入框
user_input = st.text_input("你想去哪裡？", placeholder="例如：我現在要去新竹火車站")

# 查詢按鈕
if st.button("🚀 開始 AI 導航查詢", type="primary"):
    if user_input:
        with st.spinner("AI 正在解析您的意圖並計算最佳路徑..."):
            # 呼叫後端模組
            destination = extract_destination(user_input)
            route_result = find_bus_routes(destination)
        
        st.success(f"✅ AI 成功解析目的地：**{destination}**")
        
        # 顯示路線選項卡片
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
                    
                    if st.button(f"確認搭乘此班次 ({opt['bus_route_name']})", key=opt['option_id']):
                        st.balloons()
                        st.success("🎉 已成功綁定！請上車，車載 AI 將自動為您完成無感扣款。")
        else:
            st.warning(route_result["message"])
    else:
        st.error("⚠️ 請先在上方輸入您的目的地或需求！")
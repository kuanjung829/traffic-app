import streamlit as st
import time
from database import save_db
from api_services import get_google_transit_route

def render_navigation_tab(db, user_email):
    user_data = db["users"][user_email]
    
    if not user_data["credit_card"]:
        st.error("⚠️ 請先前往左側完成「綁定信用卡」，才能啟用無感支付乘車。")
        return
        
    # 初始化 Session State
    if "route_result" not in st.session_state:
        st.session_state.route_result = None
    if "success_msg" not in st.session_state:
        st.session_state.success_msg = ""
    if "is_booked" not in st.session_state:
        st.session_state.is_booked = False

    # 如果還沒有查詢結果，顯示輸入框
    if st.session_state.route_result is None:
        col_s, col_d = st.columns(2)
        start_input = col_s.text_input("📍 出發地", placeholder="例如：清華大學")
        dest_input = col_d.text_input("🏁 目的地", placeholder="例如：新竹火車站")
        
        if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
            if start_input and dest_input:
                st.session_state.success_msg = ""
                st.session_state.is_booked = False
                with st.spinner("🚀 正在為您規劃最快路徑 (包含公車與轉乘)..."):
                    st.session_state.route_result = get_google_transit_route(start_input, dest_input)
                    st.session_state.start_loc = start_input
                    st.session_state.dest_loc = dest_input
                    st.rerun()

    # 如果已有查詢結果，顯示地圖與搭乘步驟
    else:
        result = st.session_state.route_result
        start_input = st.session_state.get("start_loc", "")
        dest_input = st.session_state.get("dest_loc", "")
        
        # ✨ 新增：返回重新搜尋按鈕
        if st.button("🔄 返回重新搜尋其他路線"):
            st.session_state.route_result = None
            st.session_state.success_msg = ""
            st.session_state.is_booked = False
            st.rerun()
            
        if result["status"] == "success":
            st.success("✅ 路線規劃成功！")
            m_col, r_col = st.columns([1.2, 1])
            
            with m_col:
                st.subheader("🗺️ 導航路徑圖")
                st.map(result["coords"], zoom=13, use_container_width=True)
            
            with r_col:
                st.subheader("💡 詳細搭乘步驟")
                st.markdown(f"**總車程預估**: `{result['travel_time']}` | **即時等候**: `{result['eta']}`")
                
                main_bus = "公車"
                with st.container(border=True):
                    for i, leg in enumerate(result["transit_legs"]):
                        if leg["type"] == "WALKING":
                            st.markdown(f"🚶‍♂️ **步行** (`{leg['duration']}`)：{leg['instruction']}")
                            
                        elif leg["type"] == "TRANSIT":
                            main_bus = leg['bus_name']
                            st.markdown(f"### 🚍 搭乘 【{leg['bus_name']}】")
                            st.caption(f"預計發車: 🕒 **{leg['dep_time']}** | 乘車時間: {leg['duration']} ({leg['num_stops']} 站)")
                            st.markdown(f"📍 **上車**：`{leg['board']}`")
                            st.markdown(f"🏁 **下車**：`{leg['alight']}`")
                            
                        if i < len(result["transit_legs"]) - 1:
                            st.markdown("👇")
                            
                    fare = result['fare'] if not user_data["is_student"] else int(result['fare'] * 0.8)
                    st.markdown(f"--- \n💵 **真實票價：NT$ {fare}** (已套用學生 8 折)")
                    
                    # 尚未扣款時顯示按鈕
                    if not st.session_state.is_booked:
                        if st.button("確認搭乘 (自動扣款)", use_container_width=True, type="primary"):
                            if user_data["balance"] >= fare:
                                user_data["balance"] -= fare
                                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                user_data["history"].append({
                                    "route": main_bus,
                                    "start": start_input,
                                    "end": dest_input,
                                    "fare": fare,
                                    "time": current_time
                                })
                                save_db(db)
                                st.session_state.is_booked = True
                                st.session_state.success_msg = f"🎉 支付成功！已扣除 NT$ {fare}，請直接上車。"
                                st.rerun()
                            else:
                                st.error("❌ 餘額不足，請至左側「儲值中心」儲值！")
                    else:
                        st.success(st.session_state.success_msg)
        else:
            st.warning(result["message"])
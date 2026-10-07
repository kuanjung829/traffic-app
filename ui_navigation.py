import streamlit as st
import time
from database import save_db
from api_services import get_google_transit_route

def render_navigation_tab(db, user_email):
    user_data = db["users"][user_email]
    
    if not user_data["credit_card"]:
        st.error("⚠️ 請先前往「💳 綁定信用卡」分頁完成綁定，才能啟用無感支付乘車。")
        return
        
    col_s, col_d = st.columns(2)
    start_input = col_s.text_input("📍 出發地", placeholder="例如：清華大學")
    dest_input = col_d.text_input("🏁 目的地", placeholder="例如：新竹南寮漁港")
    
    if st.button("🚀 開始路線查詢", type="primary", use_container_width=True):
        if start_input and dest_input:
            with st.spinner("🚀 正在呼叫 Google Maps 規劃多段路線..."):
                result = get_google_transit_route(start_input, dest_input)
                
                if result["status"] == "success":
                    st.success("✅ 路線規劃成功！")
                    m_col, r_col = st.columns([1.2, 1])
                    with m_col:
                        st.map(result["coords"], zoom=11)
                    
                    with r_col:
                        st.subheader("💡 推薦轉乘路線")
                        st.markdown(f"**第一班車即時等候**: `{result['eta']}` 分鐘 | **總車程估計**: `{result['travel_time']}`")
                        
                        with st.container(border=True):
                            for i, leg in enumerate(result["transit_legs"]):
                                st.markdown(f"**{i+1}. 🚌 搭乘 {leg['bus_name']}** (共 {leg['num_stops']} 站)")
                                st.caption(f"從 `{leg['board']}` 上車 ➔ `{leg['alight']}` 下車")
                                if i < len(result["transit_legs"]) - 1:
                                    st.markdown("👇 *轉乘*")
                                    
                            fare = result['fare'] if not user_data["is_student"] else int(result['fare']*0.8)
                            st.markdown(f"--- \n**總票價：NT$ {fare}**")
                            
                            if st.button("確認搭乘 (啟動無感支付)", use_container_width=True):
                                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                db["users"][user_email]["history"].append({
                                    "route": result["transit_legs"][0]["bus_name"] + ("等轉車" if len(result["transit_legs"])>1 else ""),
                                    "start": start_input,
                                    "end": dest_input,
                                    "fare": fare,
                                    "time": current_time
                                })
                                save_db(db)
                                st.balloons()
                                st.success("🎉 無感支付扣款成功！已記錄至雲端資料庫。")
                else:
                    st.error(result["message"])
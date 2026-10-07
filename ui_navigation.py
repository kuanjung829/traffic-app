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
            with st.spinner("🚀 正在為您規劃最快路徑 (包含步行與轉乘)..."):
                result = get_google_transit_route(start_input, dest_input)
                
                if result["status"] == "success":
                    st.success("✅ 路線規劃成功！")
                    m_col, r_col = st.columns([1.2, 1])
                    
                    with m_col:
                        st.subheader("🗺️ 路線起迄與轉乘節點")
                        # 將地圖上的點連成路徑參考
                        st.map(result["coords"], zoom=12, use_container_width=True)
                    
                    with r_col:
                        st.subheader("💡 詳細搭乘步驟")
                        st.markdown(f"**總車程預估**: `{result['travel_time']}`")
                        
                        main_bus = "公車"
                        with st.container(border=True):
                            for i, leg in enumerate(result["transit_legs"]):
                                if leg["type"] == "WALKING":
                                    st.markdown(f"🚶‍♂️ **步行** (`{leg['duration']}`)：{leg['instruction']}")
                                    
                                elif leg["type"] == "TRANSIT":
                                    main_bus = leg['bus_name']
                                    st.markdown(f"### 🚍 搭乘 【{leg['bus_name']}】")
                                    st.caption(f"預計發車時間: 🕒 **{leg['dep_time']}** | 乘車時間: {leg['duration']} ({leg['num_stops']} 站)")
                                    st.markdown(f"📍 **上車**：`{leg['board']}`")
                                    st.markdown(f"🏁 **下車**：`{leg['alight']}`")
                                    
                                if i < len(result["transit_legs"]) - 1:
                                    st.markdown("👇")
                                    
                            # 計算最終車資 (學生 8 折)
                            fare = result['fare'] if not user_data["is_student"] else int(result['fare'] * 0.8)
                            st.markdown(f"--- \n💵 **真實票價：NT$ {fare}** (已套用身分費率)")
                            
                            if st.button("確認搭乘 (自動扣款)", use_container_width=True, type="primary"):
                                if user_data["balance"] >= fare:
                                    # 扣錢並紀錄
                                    db["users"][user_email]["balance"] -= fare
                                    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                                    db["users"][user_email]["history"].append({
                                        "route": main_bus,
                                        "start": start_input,
                                        "end": dest_input,
                                        "fare": fare,
                                        "time": current_time
                                    })
                                    save_db(db)
                                    st.balloons()
                                    st.success(f"🎉 支付成功！已扣除 NT$ {fare}，請直接上車。")
                                else:
                                    st.error("❌ 餘額不足，請先至左側「儲值中心」儲值！")
                else:
                    st.error(result["message"])
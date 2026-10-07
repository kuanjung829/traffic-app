import streamlit as st
from database import load_db, save_db

# 匯入我們剛剛拆分出去的 UI 模組
from ui_auth import render_auth_page
from ui_payment import render_payment_tab
from ui_navigation import render_navigation_tab

# 初始化資料庫
db = load_db()

# 網頁基礎設定
st.set_page_config(page_title="AI 智慧公車系統", page_icon="🚌", layout="wide")

if "page" not in st.session_state: st.session_state.page = "login"
if "current_user" not in st.session_state: st.session_state.current_user = None

# ==========================================
# 頁面路由器 (Router) - 決定現在要顯示哪個畫面
# ==========================================
if st.session_state.page == "login":
    render_auth_page(db) # 呼叫登入模組
    
elif st.session_state.page == "dashboard":
    user_email = st.session_state.current_user
    user_data = db["users"][user_email]
    
    # --- 左側會員專區 ---
    with st.sidebar:
        st.title("👤 會員專區")
        if user_data["is_student"]:
            st.markdown(f"### {user_data['school_abbr']} ({user_data['name']})")
            st.success("✅ 身分優惠：學生票已啟用")
        else:
            st.markdown(f"### {user_data['name']}")
            st.info("一般帳號 (無優惠)")
        
        st.divider()
        st.markdown("### 💳 支付管理")
        if user_data["credit_card"]:
            cc_hidden = f"**** **** **** {user_data['credit_card'][-4:]}"
            st.markdown(f"**已綁定信用卡**：`{cc_hidden}`")
            if st.button("❌ 解除綁定信用卡", use_container_width=True):
                db["users"][user_email]["credit_card"] = None
                save_db(db)
                st.rerun()
        else:
            st.warning("⚠️ 尚未綁定信用卡")
            
        st.divider()
        if st.button("🚪 登出系統", use_container_width=True):
            st.session_state.current_user = None
            st.session_state.page = "login"
            st.rerun()

    # --- 右側主畫面 (交通工具與功能切換) ---
    st.title("選擇搭乘交通工具")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🚌\n\n公車系統", use_container_width=True, type="primary"): pass
    with col2: st.button("🚇\n\n捷運 (鎖定)", use_container_width=True, disabled=True)
    with col3: st.button("🚂\n\n火車 (鎖定)", use_container_width=True, disabled=True)
    with col4: st.button("🚲\n\nYouBike (鎖定)", use_container_width=True, disabled=True)
    
    st.divider()
    
    # 三個主要功能分頁
    tab1, tab2, tab3 = st.tabs(["導航：目前地 ➔ 目的地", "📍 附近站牌與路線", "💳 綁定信用卡"])
    
    with tab1:
        render_navigation_tab(db, user_email) # 呼叫導航模組
        
    with tab2:
        st.info("🚧 此功能還在開發中，敬請期待！將來可直接顯示定位點半徑 500 公尺內的站牌動態。")
        
    with tab3:
        render_payment_tab(db, user_email) # 呼叫信用卡模組
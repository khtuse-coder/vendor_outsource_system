import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 雲端連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工管理系統", layout="centered")

# 【強化視覺】CSS：加大勾選文字與標籤顯示
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #31333F !important; font-weight: bold !important; font-size: 16px !important;
    }
    .stCheckbox label p { color: #31333F !important; font-weight: bold !important; }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    /* 加大工單顯示區塊的陰影，讓它更像卡片 */
    .order-item-box { padding: 10px; border-bottom: 1px solid #eee; margin-bottom: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 委外加工管理系統")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_orders = res.data
except:
    all_orders = []

# 分類資料
pending_list = [o for o in all_orders if o.get('vendor_status') == '待接收']
working_list = [o for o in all_orders if o.get('vendor_status') == '加工中']
completed_list = [o for o in all_orders if o.get('vendor_status') == '已回貨']

tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending_list)})", 
    f"⚙️ 加工中 ({len(working_list)})", 
    f"✅ 已完工 ({len(completed_list)})"
])

# --- Tab 1 & Tab 2 邏輯不變 ---
with tab1:
    if not pending_list: st.info("目前沒有新工單")
    for order in pending_list:
        with st.container(border=True):
            st.markdown(f"### 客戶工單：{order.get('customer_wo') or '未提供'}")
            st.write(f"**預計送交數量：** {order.get('order_qty', 0)}")
            c1, c2 = st.columns(2)
            with c1:
                with st.popover("✏️ 修改數量/備註"):
                    pwd = st.text_input("管理密碼", type="password", key=f"p_e_{order['work_order']}")
                    if pwd == "5678":
                        n_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        if st.button("💾 儲存修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": n_qty}).eq("work_order", order['work_order']).execute()
                            st.rerun()
            with c2:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

with tab2:
    if not working_list: st.info("目前無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### {order.get('customer_wo') or '未提供'}")
            with st.expander("📝 完工回報 (回車確認)"):
                ret_q = st.number_input("實際回貨數量", value=int(order.get('order_qty', 0)), key=f"rq_{order['work_order']}")
                if st.button("🚀 送出完工回報", key=f"fin_{order['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (【優化】視覺放大勾選區) ---
with tab3:
    unconfirmed = [o for o in completed_list if not o.get('owner_confirmed')]
    confirmed = [o for o in completed_list if o.get('owner_confirmed')]

    if unconfirmed:
        st.subheader("📋 待確認收訖清單")
        
        # 批次操作密碼區
        with st.container(border=True):
            st.write("🔐 **批次確認驗證**")
            c_p, c_e = st.columns(2)
            bulk_pwd = c_p.text_input("確認密碼 (5678)", type="password", key="bulk_pwd")
            bulk_emp = c_e.text_input("接收工號", key="bulk_emp")
            
            selected_wos = []
            st.divider()
            
            # 【重要優化】放大顯示每一筆待確認資料
            for order in unconfirmed:
                col_sel, col_val = st.columns([1, 6])
                # 勾選框保持在左側
                if col_sel.checkbox("", key=f"check_{order['work_order']}"):
                    selected_wos.append(order['work_order'])
                
                # 文字內容大幅強化顯示
                with col_val:
                    st.markdown(f"### 📄 {order.get('customer_wo') or 'None'}")
                    st.write(f"📦 回貨數：**{order.get('return_qty', 0)}** | 機種：{order.get('customer_model') or '-'}")
                    st.caption(f"廠商回報時間：{order.get('return_time', '')[:16]}")
                    st.write("---")

            if st.button(f"✅ 批次確認收到 ({len(selected_wos)} 筆)", type="primary", disabled=len(selected_wos)==0):
                if bulk_pwd == "5678" and bulk_emp:
                    for wo in selected_wos:
                        supabase.table("vendor_orders").update({
                            "owner_confirmed": True, "confirm_emp_id": bulk_emp
                        }).eq("work_order", wo).execute()
                    st.success(f"成功接收 {len(selected_wos)} 筆工單！")
                    st.rerun()
                elif bulk_pwd != "5678": st.error("密碼錯誤")
                else: st.warning("請填寫工號")
    
    st.divider()
    st.subheader("📖 歷史收訖紀錄")
    for order in confirmed:
        with st.container(border=True):
            st.write(f"**客戶工單：** {order.get('customer_wo')} | **實收：** {order.get('return_qty')}")
            st.caption(f"接收人：{order.get('confirm_emp_id')} | 時間：{order.get('return_time', '')[:16]}")

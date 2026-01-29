import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 雲端連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工管理系統", layout="centered")

st.markdown("""
    <style>
    .stButton button { width: 100%; border-radius: 8px; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #f0f2f6; border-radius: 5px 5px 0 0; padding: 10px 20px; }
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

# --- 3. 建立分頁標籤 (顯示即時筆數) ---
tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending_list)})", 
    f"⚙️ 加工中 ({len(working_list)})", 
    f"✅ 已完工 ({len(completed_list)})"
])

# --- Tab 1: 待接收 (密碼保護修改功能) ---
with tab1:
    if not pending_list: st.write("目前沒有新工單")
    for order in pending_list:
        with st.container(border=True):
            st.markdown(f"### 客戶工單：{order.get('customer_wo') or '未提供'}")
            st.write(f"**客戶機種：** {order.get('customer_model') or '未提供'}")
            st.write(f"**預計送交數量：** {order.get('order_qty', 0)}")
            if order.get('priority'): st.warning(f"🚩 優先順序：{order.get('priority')}")
            
            c1, c2 = st.columns(2)
            with c1:
                with st.popover("✏️ 修改數量/備註"):
                    pwd = st.text_input("管理密碼", type="password", key=f"p_e_{order['work_order']}")
                    if pwd == "5678": # 密碼驗證
                        n_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        n_prio = st.text_input("優先順序", value=order.get('priority', ''), key=f"prio_e_{order['work_order']}")
                        if st.button("💾 儲存修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": n_qty, "priority": n_prio}).eq("work_order", order['work_order']).execute()
                            st.rerun()
                    elif pwd != "": st.error("密碼不正確")
            with c2:
                if st.button("📥 接收工單", key=f"acc_{order['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 2: 加工中 (完工回報) ---
with tab2:
    if not working_list: st.write("目前無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### {order.get('customer_wo') or '未提供'}")
            st.write(f"數量：{order.get('order_qty', 0)} | 機種：{order.get('customer_model') or '未提供'}")
            with st.expander("📝 完工回報"):
                ret_q = st.number_input("實回數量", value=int(order.get('order_qty', 0)), key=f"rq_{order['work_order']}")
                v_rem = st.text_area("備註說明", key=f"vr_{order['work_order']}")
                if st.button("🚀 送出回貨", key=f"fin_{order['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, 
                        "vendor_remark": v_rem, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (增加我端確認回貨功能) ---
with tab3:
    if not completed_list: st.write("尚無完工紀錄")
    for order in completed_list:
        with st.container(border=True):
            c_info, c_btn = st.columns([3, 1])
            with c_info:
                st.write(f"**客戶工單：** {order.get('customer_wo') or '未提供'}")
                st.write(f"**實回數量：** {order.get('return_qty', 0)}")
                st.caption(f"廠商回報時間：{order.get('return_time', '')[:16]}")
                if order.get('owner_confirmed'):
                    st.success(f"✅ 已由工號 {order.get('confirm_emp_id')} 確認回貨")
            
            with c_btn:
                # 僅在未確認時顯示確認按鈕
                if not order.get('owner_confirmed'):
                    with st.popover("🔘 確認回貨"):
                        cpwd = st.text_input("密碼 (5678)", type="password", key=f"cp_{order['work_order']}")
                        if cpwd == "5678": # 密碼驗證
                            emp = st.text_input("確認工號", key=f"emp_{order['work_order']}")
                            if st.button("確認收訖", key=f"cbtn_{order['work_order']}", type="primary"):
                                if emp:
                                    supabase.table("vendor_orders").update({
                                        "owner_confirmed": True, "confirm_emp_id": emp
                                    }).eq("work_order", order['work_order']).execute()
                                    st.rerun()
                                else: st.warning("請填寫工號")
                        elif cpwd != "": st.error("密碼錯誤")

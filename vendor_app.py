import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="委外管理系統", layout="centered")
st.title("🏭 委外加工管理系統")

# 抓取所有資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_orders = res.data
except:
    all_orders = []

# --- 2. 統計各狀態筆數 ---
pending_list = [o for o in all_orders if o.get('vendor_status') == '待接收']
working_list = [o for o in all_orders if o.get('vendor_status') == '加工中']
completed_list = [o for o in all_orders if o.get('vendor_status') == '已回貨']

# --- 3. 建立分頁標籤 (顯示筆數) ---
tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending_list)})", 
    f"⚙️ 加工中 ({len(working_list)})", 
    f"✅ 已完工 ({len(completed_list)})"
])

# --- Tab 1: 待接收 ---
with tab1:
    if not pending_list: st.write("無待接收工單")
    for order in pending_list:
        with st.container(border=True):
            st.markdown(f"### 客戶工單：{order.get('customer_wo', 'None')}")
            st.write(f"機種：{order.get('customer_model', 'None')} | 數量：{order.get('order_qty', 0)}")
            
            c1, c2 = st.columns(2)
            with c1:
                # 修改數量按鈕 (密碼保護)
                with st.popover("✏️ 修改數量/優先權"):
                    pwd = st.text_input("請輸入管理密碼", type="password", key=f"pwd_e_{order['work_order']}")
                    if pwd == "5678":
                        new_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        new_prio = st.text_input("優先順序", value=order.get('priority', ''), key=f"p_e_{order['work_order']}")
                        if st.button("💾 確認修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": new_qty, "priority": new_prio}).eq("work_order", order['work_order']).execute()
                            st.rerun()
                    elif pwd != "":
                        st.error("密碼錯誤")
            with c2:
                if st.button("📥 接收工單", key=f"acc_{order['work_order']}", use_container_width=True, type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 2: 加工中 ---
with tab2:
    if not working_list: st.write("無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### {order.get('customer_wo')}")
            st.write(f"數量：{order.get('order_qty')}")
            with st.expander("📝 完工回報"):
                r_qty = st.number_input("回貨數量", value=int(order.get('order_qty', 0)), key=f"r_q_{order['work_order']}")
                rem = st.text_area("備註", key=f"rem_{order['work_order']}")
                if st.button("🚀 送出回貨", key=f"fin_{order['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": r_qty, 
                        "vendor_remark": rem, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (增加確認回貨功能) ---
with tab3:
    if not completed_list: st.write("無完工紀錄")
    for order in completed_list:
        with st.container(border=True):
            col_info, col_btn = st.columns([3, 1])
            with col_info:
                st.write(f"**工單：** {order.get('customer_wo')} | **回貨數：** {order.get('return_qty')}")
                st.caption(f"回貨時間：{order.get('return_time')[:16]}")
                if order.get('owner_confirmed'):
                    st.success(f"✅ 已由工號 {order.get('confirm_emp_id')} 確認回貨")
            
            with col_btn:
                # 確認回貨按鈕 (密碼保護 + 工號輸入)
                if not order.get('owner_confirmed'):
                    with st.popover("🔘 確認回貨"):
                        cpwd = st.text_input("管理密碼", type="password", key=f"cpwd_{order['work_order']}")
                        if cpwd == "5678":
                            emp_id = st.text_input("請輸入您的工號", key=f"emp_{order['work_order']}")
                            if st.button("確認收到貨物", key=f"cbtn_{order['work_order']}", type="primary"):
                                if emp_id:
                                    supabase.table("vendor_orders").update({
                                        "owner_confirmed": True, 
                                        "confirm_emp_id": emp_id
                                    }).eq("work_order", order['work_order']).execute()
                                    st.rerun()
                                else:
                                    st.warning("請輸入工號")
                        elif cpwd != "":
                            st.error("密碼錯誤")

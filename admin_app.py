import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 連線與登入驗證 ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔐 廠內管理系統登入")
    pwd = st.text_input("請輸入管理密碼", type="password")
    if st.button("登入"):
        if pwd == "5678":
            st.session_state.logged_in = True
            st.rerun()
        else: st.error("密碼錯誤")
    st.stop()

# --- 進入管理介面 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="廠內委外管理戰情室", layout="centered")
st.title("🏢 廠內委外管理端")

# 抓取資料與儀表板 (同之前戰情版邏輯) ...
res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
all_data = res.data

# 頂部統計
m1, m2, m3 = st.columns(3)
m1.metric("廠商在庫", len([o for o in all_data if o.get('vendor_status') in ['待接收', '加工中']]))
m2.metric("待收訖", len([o for o in all_data if o.get('vendor_status') == '已回貨' and not o.get('owner_confirmed')]))
if st.button("登出"): 
    st.session_state.logged_in = False
    st.rerun()

st.divider()
query = st.text_input("🔍 搜尋工單/機種")
# ... (篩選與分類邏輯) ...

tab1, tab2, tab3 = st.tabs(["✏️ 修改資訊", "⚙️ 進度監控", "✅ 批次領收"])

with tab1: # 待接收清單，直接點開就能改數量，不用密碼
    pending = [o for o in all_data if o.get('vendor_status') == '待接收' and (not query or query.lower() in str(o).lower())]
    for o in pending:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            new_qty = st.number_input("修正數量", value=o['order_qty'], key=f"q_{o['work_order']}")
            if st.button("儲存修改", key=f"s_{o['work_order']}"):
                supabase.table("vendor_orders").update({"order_qty": new_qty}).eq("work_order", o['work_order']).execute()
                st.rerun()

with tab3: # 批次勾選領收
    unconfirmed = [o for o in all_data if o.get('vendor_status') == '已回貨' and not o.get('owner_confirmed')]
    selected_wos = []
    for o in unconfirmed:
        col_sel, col_val = st.columns([1, 6])
        if col_sel.checkbox("", key=f"ck_{o['work_order']}"): selected_wos.append(o['work_order'])
        col_val.markdown(f"**工單：** {o.get('customer_wo')} | **實回：** {o.get('return_qty')}")

    if selected_wos:
        emp = st.text_input("接收人工號", key="emp_id")
        if st.button("✅ 批次確認收到", type="primary") and emp:
            for wo in selected_wos:
                supabase.table("vendor_orders").update({"owner_confirmed": True, "confirm_emp_id": emp}).eq("work_order", wo).execute()
            st.rerun()
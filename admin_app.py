import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 登入邏輯 (改為工號登入) ---
if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

if not st.session_state.emp_id:
    st.title("🔐 廠內委外管理系統")
    user_input = st.text_input("請輸入您的員工工號以開始操作")
    if st.button("確認登入"):
        if user_input:
            st.session_state.emp_id = user_input
            st.rerun()
        else: st.warning("請填寫工號")
    st.stop()

# --- 2. 進入管理介面 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="委外管理端", layout="centered")

# CSS 強化視覺
st.markdown("""
    <style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .stButton button { width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 顯示目前操作者
st.write(f"👤 目前操作工號：**{st.session_state.emp_id}**")
if st.button("登出系統", use_container_width=False):
    st.session_state.emp_id = None
    st.rerun()

st.title("🏢 廠內管理戰情室")

# 抓取資料
res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
all_data = res.data

# 頂部統計
m1, m2 = st.columns(2)
m1.metric("廠商在庫 (加工中)", len([o for o in all_data if o['vendor_status'] in ['待接收', '加工中']]))
m2.metric("待收貨確認", len([o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']]))

st.divider()
tab1, tab2, tab3 = st.tabs(["✏️ 修改在庫資訊", "📊 全域進度監控", "✅ 批量領收確認"])

# --- Tab 1: 修改資訊 (針對廠商在庫的單子) ---
with tab1:
    st.subheader("🛠️ 修改在庫工單資訊")
    # 只顯示尚未完工的單子
    in_stock = [o for o in all_data if o['vendor_status'] in ['待接收', '加工中']]
    for o in in_stock:
        with st.container(border=True):
            st.markdown(f"### 工單：{o.get('customer_wo')}")
            st.write(f"目前狀態：{o['vendor_status']}")
            
            c1, c2 = st.columns(2)
            new_qty = c1.number_input("調整數量", value=o['order_qty'], key=f"q_{o['work_order']}")
            new_prio = c2.text_input("調整優先順序", value=o.get('priority', ''), key=f"p_{o['work_order']}")
            
            if st.button("💾 儲存修改並記錄工號", key=f"btn_{o['work_order']}"):
                # 更新時順便把操作工號記在備註或特定欄位
                supabase.table("vendor_orders").update({
                    "order_qty": new_qty, 
                    "priority": new_prio,
                    "confirm_emp_id": f"Last Edit by {st.session_state.emp_id}" # 紀錄修改者
                }).eq("work_order", o['work_order']).execute()
                st.success("修改成功")
                st.rerun()

# --- Tab 2: 監控 (略) ---

# --- Tab 3: 批量領收 (針對廠商已回報完貨的單子) ---
with tab3:
    st.subheader("📦 批量領收確認")
    to_confirm = [o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']]
    
    if not to_confirm:
        st.info("目前沒有等待領收的貨物")
    else:
        selected_wos = []
        for o in to_confirm:
            col_sel, col_val = st.columns([1, 6])
            if col_sel.checkbox("", key=f"sel_{o['work_order']}"):
                selected_wos.append(o['work_order'])
            col_val.markdown(f"**工單：** {o.get('customer_wo')} | **回貨數：** {o.get('return_qty')}")
        
        if selected_wos:
            st.divider()
            st.write(f"確認領收 **{len(selected_wos)}** 筆工單？")
            if st.button("✅ 確認收到貨物 (記錄工號)", type="primary"):
                for wo in selected_wos:
                    # 直接帶入登入時的工號
                    supabase.table("vendor_orders").update({
                        "owner_confirmed": True, 
                        "confirm_emp_id": st.session_state.emp_id
                    }).eq("work_order", wo).execute()
                st.success("領收手續完成！")
                st.rerun()

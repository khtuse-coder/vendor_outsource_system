import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 登入邏輯 (工號登入) ---
if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

if not st.session_state.emp_id:
    st.title("🏢 廠內委外管理系統")
    user_input = st.text_input("請輸入員工工號以開始")
    if st.button("確認進入"):
        if user_input:
            st.session_state.emp_id = user_input
            st.rerun()
        else: st.warning("請填寫工號")
    st.stop()

# --- 2. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="廠內管理端", layout="centered")

# 【強力視覺修正】解決文字太淡看不見的問題
st.markdown("""
    <style>
    /* 強制所有文字顯示為純黑色，提高對比度 */
    h1, h2, h3, p, span, label, .stMarkdown, .stText {
        color: #000000 !important;
        font-weight: 500 !important;
    }
    
    /* 修正 Tab 標籤文字顏色 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 16px !important;
    }

    /* 頂部狀態列樣式強化 */
    .status-bar { 
        background-color: #E8F5E9 !important; /* 淺綠色背景 */
        padding: 15px; 
        border-radius: 12px; 
        border: 2px solid #2E7D32;
        margin-bottom: 25px;
        color: #000000 !important;
        font-size: 18px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    
    /* 修正勾選框 Label 顏色 */
    .stCheckbox label p {
        color: #000000 !important;
        font-weight: bold !important;
        font-size: 18px !important;
    }

    /* 按鈕樣式 */
    .stButton button { width: 100%; font-weight: bold; height: 3em; }
    </style>
""", unsafe_allow_html=True)

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. 頂部統計列 (修正為高對比顯色) ---
in_stock_count = len([o for o in all_data if o['vendor_status'] in ['待接收', '加工中']])
to_confirm_count = len([o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']])

st.markdown(f"""
    <div class="status-bar">
        👤 <b>工號：</b> {st.session_state.emp_id} &nbsp;&nbsp;|&nbsp;&nbsp; 
        ⚙️ <b>加工中：</b> {in_stock_count} 筆 &nbsp;&nbsp;|&nbsp;&nbsp; 
        📦 <b>待收貨：</b> {to_confirm_count} 筆
    </div>
""", unsafe_allow_html=True)

if st.button("登出系統", use_container_width=False):
    st.session_state.emp_id = None
    st.rerun()

st.divider()
tab1, tab2, tab3 = st.tabs(["✏️ 修改在庫資訊", "📊 全域進度監控", "✅ 批量領收確認"])

# --- Tab 1: 修改資訊 ---
with tab1:
    in_stock = [o for o in all_data if o['vendor_status'] in ['待接收', '加工中']]
    if not in_stock: st.info("目前無在庫工單")
    for o in in_stock:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            st.write(f"機種：{o.get('customer_model')} | 目前數量：{o.get('order_qty')}")
            
            with st.expander("📝 點此修改"):
                n_qty = st.number_input("修正數量", value=o['order_qty'], key=f"q_{o['work_order']}")
                n_prio = st.text_input("優先級/備註", value=o.get('priority', ''), key=f"p_{o['work_order']}")
                if st.button("💾 儲存並更新記錄", key=f"btn_{o['work_order']}"):
                    supabase.table("vendor_orders").update({
                        "order_qty": n_qty, "priority": n_prio,
                        "confirm_emp_id": f"Edit by {st.session_state.emp_id}"
                    }).eq("work_order", o['work_order']).execute()
                    st.rerun()

# --- Tab 2: 全域進度監控 ---
with tab2:
    st.subheader("🔍 歷史與全域資料查詢")
    q = st.text_input("輸入關鍵字搜尋...")
    if all_data:
        df = pd.DataFrame(all_data)
        if q:
            df = df[df['customer_wo'].str.contains(q, na=False) | df['customer_model'].str.contains(q, na=False)]
        
        df_display = df[["customer_wo", "customer_model", "vendor_status", "order_qty", "return_qty", "confirm_emp_id"]].copy()
        df_display.columns = ["工單", "機種", "狀態", "發單數", "實收數", "最後確認人"]
        st.dataframe(df_display, use_container_width=True, hide_index=True)

# --- Tab 3: 批量領收 ---
with tab3:
    to_confirm = [o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']]
    if not to_confirm:
        st.info("目前沒有等待領收的貨物")
    else:
        st.subheader("📦 勾選收貨項目")
        selected_wos = []
        for o in to_confirm:
            with st.container(border=True):
                col_sel, col_val = st.columns([1, 6])
                if col_sel.checkbox("", key=f"sel_{o['work_order']}"):
                    selected_wos.append(o['work_order'])
                col_val.markdown(f"### 📄 {o.get('customer_wo')}")
                col_val.write(f"回貨數：**{o.get('return_qty')}** | 機種：{o.get('customer_model')}")
        
        if selected_wos:
            st.divider()
            if st.button(f"✅ 確認收到這 {len(selected_wos)} 筆貨物", type="primary"):
                for wo in selected_wos:
                    supabase.table("vendor_orders").update({
                        "owner_confirmed": True, 
                        "confirm_emp_id": st.session_state.emp_id
                    }).eq("work_order", wo).execute()
                st.success("領收成功！")
                st.rerun()

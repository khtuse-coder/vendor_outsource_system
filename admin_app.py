import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 登入邏輯 ---
if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

if not st.session_state.emp_id:
    st.set_page_config(page_title="廠內管理系統", layout="centered")
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

# 【終極視覺修正】強制亮色主題，確保黑字白底
st.markdown("""
    <style>
    /* 強制整個網頁背景為白色 */
    .stApp { background-color: #FFFFFF !important; }
    
    /* 強制所有文字為深灰色/黑色 */
    h1, h2, h3, p, span, label, div { color: #222222 !important; }
    
    /* 頂部狀態列：改為單一橫條樣式 */
    .status-bar { 
        background-color: #F1F3F4; 
        padding: 12px; 
        border-radius: 8px; 
        border: 1px solid #DADCE0;
        margin-bottom: 20px;
        font-weight: bold;
        color: #202124 !important;
    }
    
    /* 修正 Tab 文字顏色 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #202124 !important; font-weight: bold !important;
    }
    
    /* 修正卡片與勾選框 */
    .stCheckbox label p { color: #222222 !important; font-weight: bold !important; }
    [data-testid="stExpander"] { background-color: #FFFFFF !important; border: 1px solid #DDD !important; }
    
    .stButton button { width: 100%; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. 頂部狀態列 (Label + 文字) ---
in_stock_count = len([o for o in all_data if o['vendor_status'] in ['待接收', '加工中']])
to_confirm_count = len([o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']])

st.markdown(f"""
    <div class="status-bar">
        👤 工號：{st.session_state.emp_id} &nbsp; | &nbsp; 
        ⚙️ 加工中：{in_stock_count} 筆 &nbsp; | &nbsp; 
        📦 待領收：{to_confirm_count} 筆
    </div>
""", unsafe_allow_html=True)

if st.button("登出系統", use_container_width=False):
    st.session_state.emp_id = None
    st.rerun()

st.title("🏢 廠內管理戰情室")

st.divider()
tab1, tab2, tab3 = st.tabs(["✏️ 修改在庫資訊", "📊 全域進度監控", "✅ 批量領收確認"])

# --- Tab 1: 修改資訊 (廠商在庫) ---
with tab1:
    in_stock = [o for o in all_data if o['vendor_status'] in ['待接收', '加工中']]
    if not in_stock: st.info("目前無在庫工單")
    for o in in_stock:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")
            with st.expander("📝 點此修改"):
                n_qty = st.number_input("修正數量", value=o['order_qty'], key=f"q_{o['work_order']}")
                n_prio = st.text_input("優先級/備註", value=o.get('priority', ''), key=f"p_{o['work_order']}")
                if st.button("💾 儲存更新", key=f"btn_{o['work_order']}"):
                    supabase.table("vendor_orders").update({
                        "order_qty": n_qty, "priority": n_prio,
                        "confirm_emp_id": f"Edit by {st.session_state.emp_id}"
                    }).eq("work_order", o['work_order']).execute()
                    st.rerun()

# --- Tab 2: 全域進度監控 (搜尋) ---
with tab2:
    st.subheader("🔍 資料總覽與搜尋")
    q = st.text_input("輸入關鍵字 (如工單或機種)")
    if all_data:
        df = pd.DataFrame(all_data)
        if q:
            df = df[df['customer_wo'].astype(str).str.contains(q, na=False) | df['customer_model'].astype(str).str.contains(q, na=False)]
        df_show = df[["customer_wo", "customer_model", "vendor_status", "order_qty", "return_qty", "confirm_emp_id"]].copy()
        df_show.columns = ["工單", "機種", "狀態", "發單數", "實收數", "最後確認人"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# --- Tab 3: 批量領收 (待收貨) ---
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
                with col_val:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 實收：**{o.get('return_qty')}**")
        
        if selected_wos:
            st.divider()
            if st.button(f"✅ 確認收到這 {len(selected_wos)} 筆貨物", type="primary"):
                for wo in selected_wos:
                    supabase.table("vendor_orders").update({
                        "owner_confirmed": True, 
                        "confirm_emp_id": st.session_state.emp_id
                    }).eq("work_order", wo).execute()
                st.success("確認領收成功！")
                st.rerun()

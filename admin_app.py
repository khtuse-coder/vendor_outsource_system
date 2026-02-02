import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 登入邏輯 ---
if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

if not st.session_state.emp_id:
    st.set_page_config(page_title="廠內管理系統", layout="centered")
    st.markdown("""
        <style>
        .stApp { background-color: #0E1117 !important; }
        h1, label, .stTextInput input { color: #FAFAFA !important; }
        .stButton button { background-color: #00CC96 !important; color: #000 !important; font-weight: bold; }
        </style>
    """, unsafe_allow_html=True)
    
    st.title("🔐 廠內委外管理系統")
    user_input = st.text_input("請輸入員工工號以開始")
    if st.button("確認進入"):
        if user_input:
            st.session_state.emp_id = user_input
            st.rerun()
        else: st.warning("請填寫工號")
    st.stop()

# --- 2. 連線設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="廠內管理端", layout="centered")

# 【視覺重構】專業暗黑模式 CSS
st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    h1, h2, h3, p, span, label, div, li { color: #FAFAFA !important; }
    h1 { color: #00FFCC !important; font-weight: 800 !important; }
    .status-bar { 
        background-color: #262730; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #00CC96;
        margin-bottom: 20px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .ng-text { color: #FF5252 !important; font-weight: bold; font-size: 1.1em; }
    .ok-text { color: #69F0AE !important; font-weight: bold; font-size: 1.1em; }
    .stButton button { width: 100%; font-weight: bold; border-radius: 8px; }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00CC96 !important; color: #000 !important; border: none !important;
    }
    </style>
""", unsafe_allow_html=True)

# 抓取資料 (排除已結案的資料以節省效能)
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. 頂部狀態列 ---
# 統計加工中 (待接收 + 加工中) 與 待領收 (已回貨且未確認)
in_stock_count = len([o for o in all_data if o['vendor_status'] in ['待接收', '加工中']])
to_confirm_count = len([o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']])

st.markdown(f"""
    <div class="status-bar">
        👤 執行人員：{st.session_state.emp_id} &nbsp; | &nbsp; 
        ⚙️ 在庫加工：{in_stock_count} 筆 &nbsp; | &nbsp; 
        📦 待領結案：{to_confirm_count} 筆
    </div>
""", unsafe_allow_html=True)

if st.button("登出系統", type="secondary"):
    st.session_state.emp_id = None
    st.rerun()

st.title("🏢 廠內管理戰情室")
st.divider()

tab1, tab2, tab3 = st.tabs(["✏️ 修改資訊", "📊 進度監控", "✅ 領收結案"])

# --- Tab 1: 修改資訊 (針對尚未回貨的單子) ---
with tab1:
    in_stock = [o for o in all_data if o['vendor_status'] in ['待接收', '加工中']]
    if not in_stock: st.info("目前無在庫工單")
    for o in in_stock:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")
            with st.expander("📝 修正數量或優先級"):
                n_qty = st.number_input("修正數量", value=o['order_qty'], key=f"q_{o['work_order']}")
                n_prio = st.text_input("優先級/備註", value=o.get('priority', ''), key=f"p_{o['work_order']}")
                if st.button("💾 儲存更新", key=f"btn_{o['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({
                        "order_qty": n_qty, 
                        "priority": n_prio,
                        "confirm_emp_id": f"Edit by {st.session_state.emp_id}"
                    }).eq("work_order", o['work_order']).execute()
                    st.rerun()

# --- Tab 2: 全域進度監控 ---
with tab2:
    st.subheader("🔍 工單搜尋")
    q = st.text_input("輸入工單或機種關鍵字")
    if all_data:
        df = pd.DataFrame(all_data)
        if q:
            df = df[df['customer_wo'].astype(str).str.contains(q, na=False) | df['customer_model'].astype(str).str.contains(q, na=False)]
        
        df_show = df[["customer_wo", "customer_model", "vendor_status", "order_qty", "return_qty", "ok_qty", "ng_qty", "confirm_emp_id"]].copy()
        df_show.columns = ["工單", "機種", "狀態", "發單", "實收", "OK", "NG", "確認人"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# --- Tab 3: 批量領收 (點擊即結案) ---
with tab3:
    to_confirm = [o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']]
    if not to_confirm:
        st.info("目前沒有等待領收的貨物")
    else:
        st.subheader("📦 勾選欲結案項目")
        selected_wos = []
        for o in to_confirm:
            with st.container(border=True):
                col_sel, col_val = st.columns([1, 6])
                if col_sel.checkbox("", key=f"sel_{o['work_order']}"):
                    selected_wos.append(o['work_order'])
                
                with col_val:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.markdown(f"""
                    **機種：** {o.get('customer_model')} <br>
                    **總回貨：** {o.get('return_qty')} pcs &nbsp;|&nbsp; 
                    <span class='ok-text'>✅ OK：{o.get('ok_qty', 0)} pcs</span> &nbsp;|&nbsp; 
                    <span class='ng-text'>❌ NG：{o.get('ng_qty', 0)} pcs</span>
                    """, unsafe_allow_html=True)
                    if o.get('vendor_remark'):
                        st.caption(f"📝 廠商備註：{o.get('vendor_remark')}")

        if selected_wos:
            st.divider()
            # 領收動作：更新狀態為「已結案」並標記確認人
            if st.button(f"✅ 確認領收並結案 ({len(selected_wos)} 筆)", type="primary"):
                for wo in selected_wos:
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已結案",         # 更新狀態
                        "owner_confirmed": True,          # 標記已確認
                        "confirm_emp_id": st.session_state.emp_id # 紀錄員工工號
                    }).eq("work_order", wo).execute()
                st.success("🎉 選取工單已正式領收並結案！")
                st.rerun()

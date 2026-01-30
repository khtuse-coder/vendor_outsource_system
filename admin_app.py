import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 登入邏輯 ---
if "emp_id" not in st.session_state:
    st.session_state.emp_id = None

if not st.session_state.emp_id:
    st.set_page_config(page_title="廠內管理系統", layout="centered")
    # 【登入頁面暗黑化】
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
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="廠內管理端", layout="centered")

# 【視覺重構】專業暗黑模式 CSS
st.markdown("""
    <style>
    /* 1. 全局深色背景 */
    .stApp { background-color: #0E1117 !important; }
    
    /* 2. 全局文字亮白化 */
    h1, h2, h3, p, span, label, div, li { color: #FAFAFA !important; }
    h1 { color: #00FFCC !important; font-weight: 800 !important; } /* 標題用螢光綠 */
    
    /* 3. 頂部狀態列：深灰底 + 螢光邊框 */
    .status-bar { 
        background-color: #262730; 
        padding: 15px; 
        border-radius: 10px; 
        border-left: 5px solid #00CC96; /* 螢光綠飾條 */
        margin-bottom: 20px;
        font-weight: bold;
        color: #FFFFFF !important;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* 4. 分頁標籤優化 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #FAFAFA !important; font-weight: bold !important; font-size: 16px !important;
    }
    
    /* 5. 卡片與擴展區塊背景 */
    [data-testid="stExpander"] { background-color: #1E1E1E !important; border: 1px solid #444 !important; }
    .stContainer { background-color: #1E1E1E; }
    
    /* 6. 表格樣式 (深底白字) */
    [data-testid="stDataFrame"] { background-color: #262730 !important; border: 1px solid #444; }
    
    /* 7. 特殊文字顏色 (NG/OK) - 改用螢光色以利黑底閱讀 */
    .ng-text { color: #FF5252 !important; font-weight: bold; font-size: 1.1em; }
    .ok-text { color: #69F0AE !important; font-weight: bold; font-size: 1.1em; }
    
    /* 8. 按鈕樣式 */
    .stButton button { width: 100%; font-weight: bold; border-radius: 8px; }
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00CC96 !important; color: #000 !important; border: none !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #262730 !important; color: #FFF !important; border: 1px solid #555 !important;
    }
    </style>
""", unsafe_allow_html=True)

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. 頂部狀態列 ---
in_stock_count = len([o for o in all_data if o['vendor_status'] in ['待接收', '加工中']])
to_confirm_count = len([o for o in all_data if o['vendor_status'] == '已回貨' and not o['owner_confirmed']])

st.markdown(f"""
    <div class="status-bar">
        👤 工號：{st.session_state.emp_id} &nbsp; | &nbsp; 
        ⚙️ 加工中：{in_stock_count} 筆 &nbsp; | &nbsp; 
        📦 待領收：{to_confirm_count} 筆
    </div>
""", unsafe_allow_html=True)

if st.button("登出系統", type="secondary", use_container_width=False):
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
                if st.button("💾 儲存更新", key=f"btn_{o['work_order']}", type="primary"):
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
        
        # 整理顯示欄位 (包含 OK/NG)
        df_show = df[["customer_wo", "customer_model", "vendor_status", "order_qty", "return_qty", "ok_qty", "ng_qty", "confirm_emp_id"]].copy()
        df_show.columns = ["工單", "機種", "狀態", "發單", "實收", "OK", "NG", "確認人"]
        st.dataframe(df_show, use_container_width=True, hide_index=True)

# --- Tab 3: 批量領收 (待收貨 - 高亮顯示 OK/NG) ---
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
                
                # 【優化】使用螢光色顯示 OK/NG，在黑底上超明顯
                with col_val:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.markdown(f"""
                    **機種：** {o.get('customer_model')} <br>
                    **總回貨：** {o.get('return_qty')} &nbsp;|&nbsp; 
                    <span class='ok-text'>✅ OK：{o.get('ok_qty', 0)}</span> &nbsp;|&nbsp; 
                    <span class='ng-text'>❌ NG：{o.get('ng_qty', 0)}</span>
                    """, unsafe_allow_html=True)
                    
                    if o.get('vendor_remark'):
                        st.caption(f"📝 廠商備註：{o.get('vendor_remark')}")
                    st.caption(f"廠商經手人：{o.get('vendor_staff', '未填寫')}")

        if selected_wos:
            st.divider()
            # 按鈕文字改成黑色，背景螢光綠，對比度最高
            if st.button(f"✅ 確認收到這 {len(selected_wos)} 筆貨物", type="primary"):
                for wo in selected_wos:
                    supabase.table("vendor_orders").update({
                        "owner_confirmed": True, 
                        "confirm_emp_id": st.session_state.emp_id
                    }).eq("work_order", wo).execute()
                st.success("確認領收成功！")
                st.rerun()

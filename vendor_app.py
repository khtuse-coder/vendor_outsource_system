import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

# 【視覺美化】修正按鈕樣式與字體
st.markdown("""
    <style>
    /* 強制亮色背景 */
    .stApp { background-color: #FFFFFF !important; }
    
    /* 1. 字體級別放大 */
    h1 { font-size: 28px !important; color: #222 !important; font-weight: 800 !important; }
    h3 { font-size: 22px !important; color: #222 !important; font-weight: bold !important; margin-bottom: 5px !important; }
    p, span, label, div { color: #333 !important; font-size: 16px !important; }
    
    /* 2. 加大勾選框 (保持原設定) */
    [data-testid="stCheckbox"] { transform: scale(1.3); margin-left: 5px; }

    /* 3. 【修復】按鈕專屬樣式 */
    /* Primary 按鈕 (確認/全選)：紅底白字 */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #FF4B4B !important;
        color: #FFFFFF !important;
        border: none !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
        padding: 0.5rem 1rem !important;
    }
    div[data-testid="stButton"] button[kind="primary"] p {
        color: #FFFFFF !important; /* 強制內部文字為白色 */
    }

    /* Secondary 按鈕 (取消勾選)：白底灰框黑字 */
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #F0F2F6 !important;
        color: #31333F !important;
        border: 1px solid #D6D6D6 !important;
        font-size: 18px !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] p {
        color: #31333F !important; /* 強制內部文字為深色 */
    }

    /* Tab 標籤樣式 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px !important; color: #222 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

# 初始化 Session State
if "pending_select_all" not in st.session_state: st.session_state.pending_select_all = False
if "working_select_all" not in st.session_state: st.session_state.working_select_all = False

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']

tab1, tab2 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})"])

# --- Tab 1: 待接收 ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        # 【美化】全選/取消按鈕區 (使用 columns 排版)
        c_btn1, c_btn2, c_space = st.columns([1, 1, 2]) # 左邊兩個按鈕，右邊留白
        
        # 全選用 Primary (顯眼)，取消用 Secondary (低調)
        if c_btn1.button("✅ 全選", key="p_all", type="primary"): 
            st.session_state.pending_select_all = True
            st.rerun()
        if c_btn2.button("❌ 取消", key="p_none", type="secondary"): 
            st.session_state.pending_select_all = False
            st.rerun()
        
        st.write("---") # 分隔線

        selected_p = []
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}", value=st.session_state.pending_select_all):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")

        # 底部操作區
        if selected_p:
            st.markdown(f"""<div style="background-color:#E8F5E9;padding:10px;border-radius:10px;border:1px solid #4CAF50;margin-top:10px;">
                <h3 style="margin:0;color:#2E7D32!important;">📥 已選取 {len(selected_p)} 筆</h3>
            </div>""", unsafe_allow_html=True)
            
            v_name = st.text_input("請輸入領收人姓名", key="p_staff")
            if st.button("確認接收", type="primary", key="p_confirm"):
                if v_name:
                    for wo in selected_p:
                        supabase.table("vendor_orders").update({
                            "vendor_status": "加工中", "vendor_staff": v_name
                        }).eq("work_order", wo).execute()
                    st.session_state.pending_select_all = False
                    st.rerun()
                else: st.warning("請填寫姓名")

# --- Tab 2: 加工中 ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        # 全選/取消按鈕區
        w_btn1, w_btn2, w_space = st.columns([1, 1, 2])
        
        if w_btn1.button("✅ 全選", key="w_all", type="primary"): 
            st.session_state.working_select_all = True
            st.rerun()
        if w_btn2.button("❌ 取消", key="w_none", type="secondary"): 
            st.session_state.working_select_all = False
            st.rerun()

        st.write("---")

        selected_w = []
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}", value=st.session_state.working_select_all):
                    selected_w.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 加工數：{o.get('order_qty')}")

        if selected_w:
            st.markdown(f"""<div style="background-color:#FFF3E0;padding:10px;border-radius:10px;border:1px solid #FF9800;margin-top:10px;">
                <h3 style="margin:0;color:#E65100!important;">🚀 準備完工 {len(selected_w)} 筆</h3>
            </div>""", unsafe_allow_html=True)

            vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
            if st.button("確認完工送出", type="primary", key="w_confirm"):
                if vw_name:
                    for wo in selected_w:
                        orig_qty = next(x['order_qty'] for x in working if x['work_order'] == wo)
                        supabase.table("vendor_orders").update({
                            "vendor_status": "已回貨", "vendor_staff": vw_name,
                            "return_qty": orig_qty, "return_time": datetime.now().isoformat()
                        }).eq("work_order", wo).execute()
                    st.session_state.working_select_all = False
                    st.rerun()
                else: st.warning("請填寫姓名")

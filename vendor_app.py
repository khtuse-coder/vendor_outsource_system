import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

# 【視覺強化】加大字體與勾選框
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    /* 1. 字體級別放大 */
    h1 { font-size: 30px !important; color: #222 !important; }
    h3 { font-size: 24px !important; color: #222 !important; font-weight: bold !important; }
    p, span, label { font-size: 18px !important; color: #333 !important; }
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 18px !important; color: #222 !important;
    }
    
    /* 2. 加大勾選框尺寸 */
    [data-testid="stCheckbox"] { transform: scale(1.3); margin-left: 5px; }
    
    .stButton button { width: 100%; font-weight: bold; height: 3em; font-size: 16px !important; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

# 初始化 session state 用於管理勾選狀態
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

# --- Tab 1: 待接收 (增加全選/取消功能) ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        # 全選與取消按鈕
        c_btn1, c_btn2 = st.columns(2)
        if c_btn1.button("✅ 全選", key="p_all"): st.session_state.pending_select_all = True; st.rerun()
        if c_btn2.button("❌ 取消勾選", key="p_none"): st.session_state.pending_select_all = False; st.rerun()

        selected_p = []
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                # 勾選框，value 受 session_state 控制
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}", value=st.session_state.pending_select_all):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")

        if selected_p:
            with st.container(border=True):
                st.write(f"📥 **批量接收 {len(selected_p)} 筆**")
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

# --- Tab 2: 加工中 (增加全選/取消功能) ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        # 全選與取消按鈕
        w_btn1, w_btn2 = st.columns(2)
        if w_btn1.button("✅ 全選", key="w_all"): st.session_state.working_select_all = True; st.rerun()
        if w_btn2.button("❌ 取消勾選", key="w_none"): st.session_state.working_select_all = False; st.rerun()

        selected_w = []
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}", value=st.session_state.working_select_all):
                    selected_w.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 加工數：{o.get('order_qty')}")

        if selected_w:
            with st.container(border=True):
                st.write(f"🚀 **批量完工回車 {len(selected_w)} 筆**")
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

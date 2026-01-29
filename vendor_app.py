import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

# 【視覺優化】縮小字體 (縮小 4px) 並強制黑字白底
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF !important; }
    /* 縮小標題與內文字體 */
    h1 { font-size: 24px !important; color: #222 !important; }
    h3 { font-size: 18px !important; color: #222 !important; margin-bottom: 5px !important; }
    p, span, label, .stCheckbox { font-size: 13px !important; color: #333 !important; }
    
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        font-size: 14px !important; color: #222 !important;
    }
    .stButton button { width: 100%; font-weight: bold; height: 2.5em; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']

tab1, tab2 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})"])

# --- Tab 1: 待接收 (【優化】批量勾選 + 姓名輸入) ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        selected_p = []
        st.subheader("📋 勾選接收工單")
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}"):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")

        if selected_p:
            with st.container(border=True):
                st.write(f"📥 **批量接收 {len(selected_p)} 筆**")
                v_name = st.text_input("請輸入領收人姓名", key="p_staff")
                if st.button("確認接收", type="primary"):
                    if v_name:
                        for wo in selected_p:
                            supabase.table("vendor_orders").update({
                                "vendor_status": "加工中",
                                "vendor_staff": v_name
                            }).eq("work_order", wo).execute()
                        st.rerun()
                    else: st.warning("請填寫姓名")

# --- Tab 2: 加工中 (【優化】批量完工回報) ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        selected_w = []
        st.subheader("⚙️ 勾選完工回報")
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 加工數：{o.get('order_qty')}")

        if selected_w:
            with st.container(border=True):
                st.write(f"🚀 **批量完工回車 {len(selected_w)} 筆**")
                vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
                # 這裡假設批量回貨時數量等於原始發單數
                if st.button("確認完工送出", type="primary"):
                    if vw_name:
                        for wo in selected_w:
                            # 找出對應數量
                            orig_qty = next(x['order_qty'] for x in working if x['work_order'] == wo)
                            supabase.table("vendor_orders").update({
                                "vendor_status": "已回貨",
                                "vendor_staff": vw_name,
                                "return_qty": orig_qty, # 批量時預設為滿數
                                "return_time": datetime.now().isoformat()
                            }).eq("work_order", wo).execute()
                        st.rerun()
                    else: st.warning("請填寫姓名")

import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. 雲端連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工戰情系統", layout="centered")

# 【視覺修正】強制設定所有可能隱形的文字顏色
st.markdown("""
    <style>
    /* 1. 頂部儀表板 (Metric) 文字顏色修正 */
    [data-testid="stMetricValue"] > div { color: #31333F !important; font-size: 24px !important; }
    [data-testid="stMetricLabel"] > div { color: #555555 !important; font-weight: bold !important; }
    .stMetric { 
        background-color: #ffffff !important; 
        padding: 15px; border-radius: 12px; 
        box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
        border: 1px solid #dddddd !important;
    }

    /* 2. 標籤頁 (Tabs) 文字顏色修正 */
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #31333F !important; font-weight: bold !important; font-size: 16px !important;
    }

    /* 3. 勾選框 (Checkbox) 文字顏色修正 */
    .stCheckbox label p { color: #31333F !important; font-weight: bold !important; font-size: 18px !important; }

    /* 4. 按鈕通用樣式 */
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 委外加工戰情系統")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. 儀表板統計 (已修正顯色) ---
today_str = date.today().isoformat()
today_sent = len([o for o in all_data if o.get('send_time', '').startswith(today_str)])
in_vendor = len([o for o in all_data if o.get('vendor_status') in ['待接收', '加工中']])
today_done = len([o for o in all_data if o.get('vendor_status') == '已回貨' and o.get('return_time', '').startswith(today_str)])

m1, m2, m3 = st.columns(3)
with m1: st.metric("今日送出", f"{today_sent} 筆")
with m2: st.metric("廠商在庫", f"{in_vendor} 筆")
with m3: st.metric("今日回貨", f"{today_done} 筆")

st.divider()

# --- 4. 搜尋功能 ---
search_query = st.text_input("🔍 搜尋工單或機種", placeholder="請輸入關鍵字...").strip()
if search_query:
    all_orders = [o for o in all_data if search_query.lower() in str(o.get('customer_wo', '')).lower() or search_query.lower() in str(o.get('customer_model', '')).lower()]
else:
    all_orders = all_data

# 分類資料
pending_list = [o for o in all_orders if o.get('vendor_status') == '待接收']
working_list = [o for o in all_orders if o.get('vendor_status') == '加工中']
completed_list = [o for o in all_orders if o.get('vendor_status') == '已回貨']

tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending_list)})", 
    f"⚙️ 加工中 ({len(working_list)})", 
    f"✅ 已完工 ({len(completed_list)})"
])

# --- Tab 1: 待接收 (工單、機種、數量) ---
with tab1:
    if not pending_list: st.info("目前沒有新工單")
    for order in pending_list:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
            st.write(f"**機種：** {order.get('customer_model') or '未提供'}")
            st.write(f"**預計送交數量：** {order.get('order_qty', 0)}")
            
            c1, c2 = st.columns(2)
            with c1:
                with st.popover("✏️ 修改資訊"):
                    if st.text_input("管理密碼", type="password", key=f"p_e_{order['work_order']}") == "5678":
                        n_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        if st.button("💾 儲存修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": n_qty}).eq("work_order", order['work_order']).execute()
                            st.rerun()
            with c2:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 2: 加工中 (工單、機種、數量) ---
with tab2:
    if not working_list: st.info("目前無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
            st.write(f"**機種：** {order.get('customer_model') or '未提供'} | **預計數：** {order.get('order_qty', 0)}")
            with st.expander("📝 完工回報 (回車確認)"):
                ret_q = st.number_input("實際回貨數量", value=int(order.get('order_qty', 0)), key=f"rq_{order['work_order']}")
                if ret_q != order.get('order_qty', 0):
                    st.warning(f"⚠️ 注意：回貨數量與原始數量不符")
                if st.button("🚀 送出完工回報", key=f"fin_{order['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (先勾選，後簽核) ---
with tab3:
    unconfirmed = [o for o in completed_list if not o.get('owner_confirmed')]
    confirmed = [o for o in completed_list if o.get('owner_confirmed')]

    if unconfirmed:
        st.subheader("📋 待確認收訖清單 (請勾選)")
        selected_wos = []
        for order in unconfirmed:
            with st.container(border=True):
                col_sel, col_val = st.columns([1, 6])
                if col_sel.checkbox("", key=f"check_{order['work_order']}"):
                    selected_wos.append(order['work_order'])
                with col_val:
                    st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
                    st.write(f"**機種：** {order.get('customer_model') or '-'} | 📦 回貨：**{order.get('return_qty', 0)}**")

        st.divider()
        if selected_wos:
            with st.container(border=True):
                st.write(f"🔒 **確認接收 {len(selected_wos)} 筆工單**")
                c_p, c_e = st.columns(2)
                if c_p.text_input("密碼 (5678)", type="password", key="bulk_p") == "5678":
                    emp = c_e.text_input("接收工號", key="bulk_e")
                    if st.button("✅ 批次確認收到", type="primary"):
                        if emp:
                            for wo in selected_wos:
                                supabase.table("vendor_orders").update({"owner_confirmed": True, "confirm_emp_id": emp}).eq("work_order", wo).execute()
                            st.rerun()
                        else: st.warning("請填寫工號")
        else:
            st.info("💡 請先勾選上方要確認回貨的工單。")
    
    st.divider()
    st.subheader("📖 歷史收訖紀錄")
    for order in confirmed:
        with st.container(border=True):
            st.write(f"**工單：** {order.get('customer_wo')} | **機種：** {order.get('customer_model')}")
            st.write(f"**實收：** {order.get('return_qty')} | **接收人：** {order.get('confirm_emp_id')}")
            st.caption(f"時間：{order.get('return_time', '')[:16]}")

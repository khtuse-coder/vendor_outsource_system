import streamlit as st
from supabase import create_client
from datetime import datetime, date

# --- 1. 雲端連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工戰情系統", layout="centered")

# 【優化】視覺樣式：增加急件邊框與標籤顏色
st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #31333F !important; font-weight: bold !important; font-size: 16px !important;
    }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 10px; border: 1px solid #eee; }
    .urgent-card { border: 2px solid #FF4B4B !important; background-color: #FFF5F5; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    .normal-card { border: 1px solid #ddd; border-radius: 10px; padding: 10px; margin-bottom: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("🚀 委外加工戰情系統")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# --- 3. [新增] 頂部儀表板統計 ---
today_str = date.today().isoformat()
today_sent = len([o for o in all_data if o.get('send_time', '').startswith(today_str)])
in_vendor = len([o for o in all_data if o.get('vendor_status') in ['待接收', '加工中']])
today_done = len([o for o in all_data if o.get('vendor_status') == '已回貨' and o.get('return_time', '').startswith(today_str)])

m1, m2, m3 = st.columns(3)
m1.metric("今日送出", f"{today_sent} 筆")
m2.metric("廠商在庫", f"{in_vendor} 筆", delta_color="inverse")
m3.metric("今日回貨", f"{today_done} 筆")

st.divider()

# --- 4. [新增] 搜尋與篩選功能 ---
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

# --- Tab 1: 待接收 ---
with tab1:
    if not pending_list: st.info("無相符工單")
    for order in pending_list:
        # [優化] 急件特殊樣式
        is_urgent = order.get('priority') is not None and order.get('priority') != ""
        card_class = "urgent-card" if is_urgent else "normal-card"
        
        with st.container(border=True):
            if is_urgent: st.error(f"🚨 急件優先：{order.get('priority')}")
            st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
            st.write(f"**機種：** {order.get('customer_model') or '未提供'}")
            st.write(f"**預計送交數量：** {order.get('order_qty', 0)}")
            
            c1, c2 = st.columns(2)
            with c1:
                with st.popover("✏️ 修改資訊"):
                    pwd = st.text_input("管理密碼", type="password", key=f"p_e_{order['work_order']}")
                    if pwd == "5678":
                        n_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        n_prio = st.text_input("優先級/備註", value=order.get('priority', ''), key=f"prio_e_{order['work_order']}")
                        if st.button("💾 儲存修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": n_qty, "priority": n_prio}).eq("work_order", order['work_order']).execute()
                            st.rerun()
            with c2:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 2: 加工中 (新增數量異常防呆) ---
with tab2:
    if not working_list: st.info("目前無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
            st.write(f"**機種：** {order.get('customer_model') or '未提供'} | **預計數：** {order.get('order_qty', 0)}")
            
            with st.expander("📝 完工回報"):
                ret_q = st.number_input("實際回貨數量", value=int(order.get('order_qty', 0)), key=f"rq_{order['work_order']}")
                
                # [新增] 數量異常防呆提醒
                if ret_q != order.get('order_qty', 0):
                    st.warning(f"⚠️ 注意：回貨數量與原始數量不符 (差異: {ret_q - order.get('order_qty', 0)})")
                
                v_rem = st.text_area("回車/狀況備註", key=f"vr_{order['work_order']}")
                
                if st.button("🚀 送出完工回報", key=f"fin_{order['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, 
                        "vendor_remark": v_rem, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (批次確認) ---
with tab3:
    unconfirmed = [o for o in completed_list if not o.get('owner_confirmed')]
    confirmed = [o for o in completed_list if o.get('owner_confirmed')]

    if unconfirmed:
        st.subheader("📋 待接收確認 (請勾選)")
        selected_wos = []
        for order in unconfirmed:
            with st.container(border=True):
                col_sel, col_val = st.columns([1, 6])
                if col_sel.checkbox("", key=f"check_{order['work_order']}"):
                    selected_wos.append(order['work_order'])
                with col_val:
                    st.markdown(f"### 📄 工單：{order.get('customer_wo') or 'None'}")
                    st.write(f"**機種：** {order.get('customer_model')} | 📦 回貨：**{order.get('return_qty', 0)}**")

        if selected_wos:
            with st.container(border=True):
                st.write(f"🔒 **批次確認 {len(selected_wos)} 筆**")
                c_p, c_e = st.columns(2)
                if c_p.text_input("密碼", type="password", key="bulk_p") == "5678":
                    emp = c_e.text_input("工號", key="bulk_e")
                    if st.button("✅ 批次確認收訖", type="primary"):
                        if emp:
                            for wo in selected_wos:
                                supabase.table("vendor_orders").update({"owner_confirmed": True, "confirm_emp_id": emp}).eq("work_order", wo).execute()
                            st.rerun()
                        else: st.warning("請輸入工號")
    
    st.divider()
    st.subheader("📖 歷史紀錄")
    # 使用表格顯示歷史紀錄，方便快速搜尋與對帳
    if confirmed:
        st.dataframe(
            confirmed,
            column_order=("customer_wo", "customer_model", "return_qty", "confirm_emp_id", "return_time"),
            column_config={"customer_wo":"工單", "customer_model":"機種", "return_qty":"實收", "confirm_emp_id":"確認人", "return_time":"時間"},
            hide_index=True
        )

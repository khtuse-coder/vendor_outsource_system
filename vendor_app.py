import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 雲端連線設定 ---
# 這裡使用你的 Supabase 憑證
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工回報系統", layout="centered")

# 自定義 CSS 優化手機閱讀體驗
st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 24px; }
    .stButton button { width: 100%; border-radius: 10px; }
    .order-card { padding: 15px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 15px; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端工單系統")

# 分頁標籤：待接收 -> 加工中 -> 已完工
tab1, tab2, tab3 = st.tabs(["🆕 待接收", "⚙️ 加工中", "✅ 已完工"])

# 從雲端抓取最新資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_orders = res.data
except Exception as e:
    st.error(f"資料讀取失敗: {e}")
    all_orders = []

# --- 功能：更新資料庫狀態 ---
def update_order(wo, update_data):
    supabase.table("vendor_orders").update(update_data).eq("work_order", wo).execute()
    st.rerun()

# --- Tab 1: 待接收 (可修改數量與優先順序) ---
with tab1:
    pending_orders = [o for o in all_orders if o.get('vendor_status') == '待接收']
    if not pending_orders:
        st.write("目前沒有待處理的新工單。")
    
    for order in pending_orders:
        with st.container(border=True):
            # 優先顯示客戶資訊
            c_wo = order.get('customer_wo') or "未提供工單"
            c_model = order.get('customer_model') or "未提供機種"
            
            st.markdown(f"### 客戶工單：{c_wo}")
            st.write(f"**客戶機種：** {c_model}")
            st.write(f"**預計送交數量：** {order.get('order_qty', 0)}")
            
            # 顯示優先順序標籤
            priority = order.get('priority')
            if priority:
                st.warning(f"🚩 優先順序：{priority}")
            
            col_edit, col_acc = st.columns(2)
            
            # 功能：修改數量與備註
            with col_edit:
                with st.popover("✏️ 修改數量/備註"):
                    new_qty = st.number_input("修正送交數量", value=int(order.get('order_qty', 0)), key=f"q_edit_{order['work_order']}")
                    new_prio = st.text_input("備註優先順序", value=priority if priority else "", key=f"p_edit_{order['work_order']}")
                    if st.button("💾 儲存修改", key=f"save_{order['work_order']}"):
                        update_order(order['work_order'], {"order_qty": new_qty, "priority": new_prio})
            
            # 功能：確認接收
            with col_acc:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary"):
                    update_order(order['work_order'], {"vendor_status": "加工中"})

# --- Tab 2: 加工中 (回報完工) ---
with tab2:
    working_orders = [o for o in all_orders if o.get('vendor_status') == '加工中']
    if not working_orders:
        st.write("目前沒有加工中的工單。")
        
    for order in working_orders:
        with st.container(border=True):
            st.markdown(f"### 🛠️ {order.get('customer_wo')}")
            st.write(f"**機種：** {order.get('customer_model')}")
            st.write(f"**數量：** {order.get('order_qty')}")
            
            with st.expander("📝 完工回報單"):
                ret_qty = st.number_input("實際回貨數量", value=int(order.get('order_qty', 0)), key=f"ret_q_{order['work_order']}")
                v_remark = st.text_area("加工狀況備註", placeholder="如有缺料、不良或特殊狀況請在此說明", key=f"v_rem_{order['work_order']}")
                if st.button("🚀 回報完工", key=f"finish_{order['work_order']}", use_container_width=True):
                    finish_payload = {
                        "vendor_status": "已回貨",
                        "return_qty": ret_qty,
                        "vendor_remark": v_remark,
                        "return_time": datetime.now().isoformat()
                    }
                    update_order(order['work_order'], finish_payload)

# --- Tab 3: 已完工 (歷史紀錄查詢) ---
with tab3:
    completed_orders = [o for o in all_orders if o.get('vendor_status') == '已回貨']
    if not completed_orders:
        st.write("尚無完工紀錄。")
    else:
        # 歷史紀錄使用表格顯示，方便廠商對帳
        st.dataframe(
            completed_orders,
            column_order=("customer_wo", "customer_model", "return_qty", "return_time", "vendor_remark"),
            column_config={
                "customer_wo": "客戶工單",
                "customer_model": "客戶機種",
                "return_qty": "回貨數",
                "return_time": "完工時間",
                "vendor_remark": "備註"
            },
            hide_index=True,
            use_container_width=True
        )

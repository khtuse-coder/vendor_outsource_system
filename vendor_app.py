import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 雲端連線設定 ---
# 這裡建議使用與班表 App 相同的金鑰，但連接到不同的資料表
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁介面配置 ---
st.set_page_config(page_title="委外加工回報系統", layout="wide")
st.title("🏭 委外加工進度回報")

# 使用分頁標籤分類工單
tab1, tab2, tab3 = st.tabs(["🆕 待接收", "⚙️ 加工中", "✅ 已完工"])

# 抓取雲端資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_orders = res.data
except Exception as e:
    st.error(f"連線失敗: {e}")
    all_orders = []

# --- 功能函式：更新狀態 ---
def update_status(wo, new_status, extra_data=None):
    update_payload = {"vendor_status": new_status}
    if extra_data:
        update_payload.update(extra_data)
    supabase.table("vendor_orders").update(update_payload).eq("work_order", wo).execute()
    st.rerun()

# --- Tab 1: 待接收 (尚未確認的工單) ---
with tab1:
    pending_orders = [o for o in all_orders if o['vendor_status'] == '待接收']
    if not pending_orders:
        st.write("目前沒有新工單")
    for order in pending_orders:
        with st.container(border=True):
            c1, c2, c3 = st.columns([2, 2, 1])
            c1.markdown(f"**工單：** {order['work_order']}\n\n**機種：** {order['model_name']}")
            c2.markdown(f"**數量：** {order['order_qty']}\n\n**送出時間：** {order['send_time'][:16]}")
            if c3.button("📥 接收", key=f"acc_{order['work_order']}", use_container_width=True):
                update_status(order['work_order'], "加工中")

# --- Tab 2: 加工中 (生產中，準備回報數量) ---
with tab2:
    working_orders = [o for o in all_orders if o['vendor_status'] == '加工中']
    if not working_orders:
        st.write("目前沒有加工中的工單")
    for order in working_orders:
        with st.container(border=True):
            st.markdown(f"### 🛠️ {order['work_order']} ({order['model_name']})")
            st.write(f"預計數量: {order['order_qty']}")
            
            with st.expander("📝 填寫完工回報"):
                ret_qty = st.number_input("實際回貨數量", value=order['order_qty'], key=f"q_{order['work_order']}")
                remark = st.text_area("狀況備註", placeholder="如有缺料或不良請註明", key=f"r_{order['work_order']}")
                if st.button("🚀 回報完工並送出", key=f"fin_{order['work_order']}", use_container_width=True):
                    finish_data = {
                        "return_qty": ret_qty,
                        "vendor_remark": remark,
                        "return_time": datetime.now().isoformat()
                    }
                    update_status(order['work_order'], "已回貨", finish_data)

# --- Tab 3: 已完工 (歷史紀錄) ---
with tab3:
    completed_orders = [o for o in all_orders if o['vendor_status'] == '已回貨']
    if not completed_orders:
        st.write("尚無完工紀錄")
    else:
        # 用表格顯示歷史紀錄比較整齊
        st.dataframe(completed_orders, use_container_width=True, hide_index=True,
                     column_order=("work_order", "model_name", "return_qty", "return_time", "vendor_remark"))
import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="委外加工回報", layout="centered")
st.title("📦 廠商端工單系統")

tab1, tab2, tab3 = st.tabs(["🆕 待接收", "⚙️ 加工中", "✅ 已完工"])

# 抓取資料
res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
all_orders = res.data

# --- Tab 1: 待接收 (增加修改功能) ---
with tab1:
    pending = [o for o in all_orders if o['vendor_status'] == '待接收']
    for order in pending:
        with st.container(border=True):
            # 1. 顯示客戶資訊
            st.markdown(f"### 客戶工單：{order['customer_wo']}")
            st.write(f"**客戶機種：** {order['customer_model']}")
            st.write(f"**預計送交數量：** {order['order_qty']}")
            if order.get('priority'):
                st.warning(f"🚩 優先順序：{order['priority']}")
            
            col1, col2 = st.columns(2)
            # 2. 修改按鈕：讓廠商微調數量與標記優先級
            with col1:
                with st.popover("✏️ 修改數量/備註"):
                    new_qty = st.number_input("修改數量", value=order['order_qty'], key=f"edit_q_{order['work_order']}")
                    new_prio = st.text_input("備註優先順序", value=order.get('priority', ''), key=f"edit_p_{order['work_order']}")
                    if st.button("💾 儲存修改", key=f"save_{order['work_order']}"):
                        supabase.table("vendor_orders").update({"order_qty": new_qty, "priority": new_prio}).eq("work_order", order['work_order']).execute()
                        st.rerun()
            
            with col2:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary", use_container_width=True):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 2: 加工中 (不變) ---
with tab2:
    working = [o for o in all_orders if o['vendor_status'] == '加工中']
    for order in working:
        with st.container(border=True):
            st.write(f"**客戶工單：** {order['customer_wo']}")
            st.write(f"**客戶機種：** {order['customer_model']}")
            st.write(f"**數量：** {order['order_qty']}")
            with st.expander("📝 完工回報"):
                ret_qty = st.number_input("實回數量", value=order['order_qty'], key=f"ret_{order['work_order']}")
                rem = st.text_area("備註", key=f"rem_{order['work_order']}")
                if st.button("🚀 送出回貨", key=f"fin_{order['work_order']}"):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_qty, 
                        "vendor_remark": rem, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (列表簡化) ---
with tab3:
    done = [o for o in all_orders if o['vendor_status'] == '已回貨']
    st.dataframe(done, column_order=("customer_wo", "customer_model", "return_qty", "return_time"), hide_index=True)

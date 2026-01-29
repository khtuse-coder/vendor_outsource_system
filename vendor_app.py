import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="廠商加工回報系統", layout="centered")
st.title("📦 廠商端加工回報")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']

t1, t2 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})"])

with t1:
    for o in pending:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            st.write(f"**機種：** {o.get('customer_model')} | **數量：** {o.get('order_qty')}")
            if st.button("📥 確認接收", key=f"acc_{o['work_order']}", type="primary"):
                supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", o['work_order']).execute()
                st.rerun()

with t2:
    for o in working:
        with st.container(border=True):
            st.markdown(f"### 📄 工單：{o.get('customer_wo')}")
            st.write(f"**機種：** {o.get('customer_model')} | **數量：** {o.get('order_qty')}")
            with st.expander("📝 完工回報"):
                ret_q = st.number_input("實際回貨數", value=int(o.get('order_qty', 0)), key=f"rq_{o['work_order']}")
                v_rem = st.text_area("備註", key=f"vr_{o['work_order']}")
                if st.button("🚀 送出完工", key=f"fin_{o['work_order']}", use_container_width=True):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, 
                        "vendor_remark": v_rem, "return_time": datetime.now().isoformat()
                    }).eq("work_order", o['work_order']).execute()
                    st.rerun()

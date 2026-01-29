import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 雲端連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="委外加工管理系統", layout="centered")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] button [data-testid="stMarkdownContainer"] p {
        color: #31333F !important; font-weight: bold !important; font-size: 16px !important;
    }
    .stButton button { width: 100%; border-radius: 8px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 委外加工管理系統")

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_orders = res.data
except:
    all_orders = []

pending_list = [o for o in all_orders if o.get('vendor_status') == '待接收']
working_list = [o for o in all_orders if o.get('vendor_status') == '加工中']
completed_list = [o for o in all_orders if o.get('vendor_status') == '已回貨']

tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending_list)})", 
    f"⚙️ 加工中 ({len(working_list)})", 
    f"✅ 已完工 ({len(completed_list)})"
])

# --- Tab 1 & 2 保持原樣 ---
with tab1:
    if not pending_list: st.info("目前沒有新工單")
    for order in pending_list:
        with st.container(border=True):
            st.markdown(f"### 客戶工單：{order.get('customer_wo') or '未提供'}")
            st.write(f"**預計數量：** {order.get('order_qty', 0)}")
            c1, c2 = st.columns(2)
            with c1:
                with st.popover("✏️ 修改數量/備註"):
                    pwd = st.text_input("管理密碼", type="password", key=f"p_e_{order['work_order']}")
                    if pwd == "5678":
                        n_qty = st.number_input("修正數量", value=int(order.get('order_qty', 0)), key=f"q_e_{order['work_order']}")
                        if st.button("💾 儲存修改", key=f"s_e_{order['work_order']}"):
                            supabase.table("vendor_orders").update({"order_qty": n_qty}).eq("work_order", order['work_order']).execute()
                            st.rerun()
            with c2:
                if st.button("📥 確認接收", key=f"acc_{order['work_order']}", type="primary"):
                    supabase.table("vendor_orders").update({"vendor_status": "加工中"}).eq("work_order", order['work_order']).execute()
                    st.rerun()

with tab2:
    if not working_list: st.info("目前無加工中工單")
    for order in working_list:
        with st.container(border=True):
            st.markdown(f"### {order.get('customer_wo') or '未提供'}")
            with st.expander("📝 完工回報"):
                ret_q = st.number_input("實際回貨數量", value=int(order.get('order_qty', 0)), key=f"rq_{order['work_order']}")
                if st.button("🚀 送出完工回報", key=f"fin_{order['work_order']}"):
                    supabase.table("vendor_orders").update({
                        "vendor_status": "已回貨", "return_qty": ret_q, "return_time": datetime.now().isoformat()
                    }).eq("work_order", order['work_order']).execute()
                    st.rerun()

# --- Tab 3: 已完工 (【新增】多筆勾選功能) ---
with tab3:
    if not completed_list:
        st.info("尚無完工紀錄")
    else:
        # 分出「尚未確認」與「已確認」的資料
        unconfirmed = [o for o in completed_list if not o.get('owner_confirmed')]
        confirmed = [o for o in completed_list if o.get('owner_confirmed')]

        if unconfirmed:
            st.subheader("📋 批次確認回貨")
            # 將資料轉成 DataFrame 方便顯示與選取
            df_unconfirmed = pd.DataFrame(unconfirmed)
            # 簡化顯示的欄位
            df_show = df_unconfirmed[["work_order", "customer_wo", "customer_model", "return_qty"]].copy()
            df_show.columns = ["內部編號", "客戶工單", "客戶機種", "回貨數"]

            # 使用可選取的表格
            selected_data = st.dataframe(
                df_show,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="multi_row"
            )

            # 取得被選取的行數
            selected_rows = selected_data.selection.rows
            
            if selected_rows:
                # 取得被選取的工單號碼清單
                selected_wo_list = df_show.iloc[selected_rows]["內部編號"].tolist()
                st.success(f"已選取 {len(selected_wo_list)} 筆工單")

                with st.container(border=True):
                    st.write("🔒 **請輸入管理資訊進行批次確認**")
                    c1, c2 = st.columns(2)
                    bulk_pwd = c1.text_input("密碼 (5678)", type="password", key="bulk_pwd")
                    bulk_emp = c2.text_input("確認人工號", key="bulk_emp")
                    
                    if st.button("✅ 批次確認收訖", type="primary"):
                        if bulk_pwd == "5678" and bulk_emp:
                            # 循環更新每一筆選取的工單
                            for wo in selected_wo_list:
                                supabase.table("vendor_orders").update({
                                    "owner_confirmed": True, 
                                    "confirm_emp_id": bulk_emp
                                }).eq("work_order", wo).execute()
                            st.toast(f"成功確認 {len(selected_wo_list)} 筆資料！")
                            st.rerun()
                        elif bulk_pwd != "5678":
                            st.error("密碼錯誤")
                        else:
                            st.warning("請填寫工號")
            else:
                st.info("💡 請點擊下方表格左側勾選要確認的項目")
        
        st.divider()
        st.subheader("📖 歷史已確認紀錄")
        if confirmed:
            st.dataframe(
                pd.DataFrame(confirmed),
                column_order=("customer_wo", "customer_model", "return_qty", "confirm_emp_id"),
                column_config={"customer_wo":"工單", "customer_model":"機種", "return_qty":"數量", "confirm_emp_id":"確認人"},
                hide_index=True,
                use_container_width=True
            )

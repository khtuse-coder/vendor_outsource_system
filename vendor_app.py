import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import requests
import json

# --- 1. 基礎設定與 LINE 通知 ---
#LINE_ACCESS_TOKEN = st.secrets["LINE_TOKEN"]

# def send_line_msg(text):
#     """透過 LINE 廣播模式發送通知"""
#     try:
#         url = "https://api.line.me/v2/bot/message/broadcast"
#         headers = {
#             "Content-Type": "application/json",
#             "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
#         }
#         payload = {
#             "messages": [{"type": "text", "text": text}]
#         }
#         response = requests.post(url, headers=headers, data=json.dumps(payload))
#         if response.status_code != 200:
#             print(f"LINE 發送失敗: {response.text}")
#     except Exception as e:
#         print(f"LINE 發生錯誤: {e}")

# --- 2. 連線設定 ---
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報系統", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, label, div, span { color: #FAFAFA !important; }
    h1 { font-size: 26px !important; font-weight: 800 !important; color: #00FFCC !important; }
    .report-card { background-color: #1E1E1E; border: 1px solid #444; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    /* 優先級標籤樣式 */
    .priority-tag { background-color: #004d40; color: #00FFCC; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
    /* 需求日標籤樣式 */
    .date-tag { background-color: #3e2723; color: #FFAB91; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; border: 1px solid #FFAB91; margin-left: 5px; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

# --- 4. 資料讀取 ---
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

# 分類數據
pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']
completed = [o for o in all_data if o.get('vendor_status') == '已回貨']

tab1, tab2, tab3 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})", f"📜 歷史紀錄"])

# --- Tab 1: 待接收 ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        c1, c2, _ = st.columns([0.8, 0.8, 2.4]) 
        with c1:
            if st.button("✅ 全選", key="p_all", type="primary"):
                for o in pending: st.session_state[f"p_ck_{o['work_order']}"] = True
                st.rerun()
        with c2:
            if st.button("❌ 取消", key="p_none", type="secondary"):
                for o in pending: st.session_state[f"p_ck_{o['work_order']}"] = False
                st.rerun()
        
        selected_p = []
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 9])
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}"):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    # 按照順序顯示：機種、數量、需求日、優先
                    model = o.get('customer_model', '-')
                    qty = o.get('order_qty', 0)
                    due = o.get('due_date', '未設定')
                    prio = o.get('priority', '一般')
                    st.write(f"機種：{model} | 數量：{qty} | 📅 需求日：{due} | ⚡ 優先：{prio}")

        if selected_p:
            st.markdown(f'<div class="report-card" style="border-color:#00CC96;">📥 準備接收 {len(selected_p)} 筆工單</div>', unsafe_allow_html=True)
            v_name = st.text_input("請輸入領收人姓名", key="p_staff")
            if st.button("確認接收", type="primary", key="p_confirm"):
                if v_name:
                    for wo in selected_p:
                        supabase.table("vendor_orders").update({
                            "vendor_status": "加工中", 
                            "vendor_staff": v_name
                        }).eq("work_order", wo).execute()
                    st.success("接收成功！")
                    st.rerun()
                else: st.warning("請填寫姓名")

# --- Tab 2: 加工中 ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        c1, c2, _ = st.columns([0.8, 0.8, 2.4])
        with c1:
            if st.button("✅ 全選", key="w_all", type="primary"): 
                for o in working: st.session_state[f"w_ck_{o['work_order']}"] = True
                st.rerun()
        with c2:
            if st.button("❌ 取消", key="w_none", type="secondary"): 
                for o in working: st.session_state[f"w_ck_{o['work_order']}"] = False
                st.rerun()

        selected_w_data = []
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 9])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w_data.append(o)
                with c_info:
                    due = o.get('due_date', '未設定')
                    prio = o.get('priority', '一般')
                    # 同時顯示需求日標籤與優先級標籤
                    st.markdown(f"### 📄 {o.get('customer_wo')} <span class='date-tag'>📅 {due}</span> <span class='priority-tag'>⚡ {prio}</span>", unsafe_allow_html=True)
                    st.write(f"機種：{o.get('customer_model')} | 發單數：{o.get('order_qty')}")

        if selected_w_data:
            st.write("---")
            for item in selected_w_data:
                wo_id = item['work_order']
                qty = item['order_qty']
                with st.container():
                    st.markdown(f'<div class="report-card"><h4>📄 {item["customer_wo"]}</h4><p>總數：{qty}</p></div>', unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 2])
                    ng_val = c1.number_input("❌ NG 數量", min_value=0, max_value=qty, value=0, key=f"ng_in_{wo_id}")
                    rem_val = c2.text_input("📝 備註", key=f"rem_in_{wo_id}")
                    st.caption(f"✅ 良品 (OK)： **{qty - ng_val}**")

            vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
            if st.button("確認完工送出", type="primary", key="w_confirm"):
                if vw_name:
                    for item in selected_w_data:
                        wo_id = item['work_order']
                        qty = item['order_qty']
                        final_ng = st.session_state[f"ng_in_{wo_id}"]
                        final_rem = st.session_state[f"rem_in_{wo_id}"]
                        
                        supabase.table("vendor_orders").update({
                            "vendor_status": "已回貨", 
                            "vendor_staff": vw_name,
                            "return_qty": qty, 
                            "ok_qty": qty - final_ng, 
                            "ng_qty": final_ng,
                            "vendor_remark": final_rem, 
                            "return_time": datetime.now().isoformat()
                        }).eq("work_order", wo_id).execute()
                        
                        msg = f"🚀 廠商已回報完工\n📄 工單：{item['customer_wo']}\n✅ 良品：{qty - final_ng}\n❌ NG：{final_ng}\n👤 經手人：{vw_name}"
                        if final_rem: msg += f"\n📝 備註：{final_rem}"
                        send_line_msg(msg)

                    st.success("回報成功！LINE 通知已發送")
                    st.rerun()
                else: st.warning("請填寫姓名")

# --- Tab 3: 歷史紀錄 ---
with tab3:
    st.markdown("### 🔍 完工履歷查詢")
    search_q = st.text_input("輸入工單號碼或機種搜尋...", key="hist_search")
    if completed:
        df = pd.DataFrame(completed)
        if search_q:
            df = df[df['customer_wo'].astype(str).str.contains(search_q, case=False) | df['customer_model'].astype(str).str.contains(search_q, case=False)]
        
        if not df.empty:
            df["return_time"] = df["return_time"].apply(lambda x: x[:16].replace('T', ' ') if x else '-')
            # 表格排列：加入需求日與優先級
            df_show = df[["return_time", "customer_wo", "customer_model", "order_qty", "due_date", "priority", "ok_qty", "ng_qty", "vendor_staff", "vendor_remark"]].copy()
            df_show.columns = ["回貨時間", "工單", "機種", "發單數", "需求日", "優先級", "OK", "NG", "經手人", "備註"]
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else: st.warning("查無資料")
    else: st.info("尚無歷史紀錄")


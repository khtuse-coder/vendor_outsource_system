import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd
import requests
import json

# --- 🔥 LINE 設定 (我幫你修好空格了，直接用這串) ---
LINE_ACCESS_TOKEN = "EHUErtlRZf95o8W0hqmME0iNvKjNdWCKYc3cApNomcgjJP9InqHM3zjIN0tvt9ViZO/LDsC4R7eV4G8Ka/gfY0gTLbikYN4hRo5ll4xNW7tG92IxVjgwgaIBBbJaG95gz5iJwbKAIDTk1neRQt9SugdB04t89/1O/w1cDnyilFU="

def send_line_msg(text):
    """透過 LINE 廣播模式發送通知 (不用 User ID)"""
    try:
        # 改用 broadcast (廣播) 端點
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
        }
        payload = {
            "messages": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
        # 發送請求
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        
        # 檢查是否成功
        if response.status_code != 200:
            print(f"LINE 發送失敗: {response.text}")
    except Exception as e:
        print(f"LINE 發生錯誤: {e}")

# --- 2. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 3. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117 !important; }
    h1, h2, h3, h4, p, label, div, span { color: #FAFAFA !important; }
    h1 { font-size: 26px !important; font-weight: 800 !important; color: #00FFCC !important; }
    [data-testid="stCheckbox"] { transform: scale(1.3); margin-right: 5px; }
    .stNumberInput input, .stTextInput input { min-height: 45px; font-size: 16px; background-color: #262730; color: white; border: 1px solid #444; }
    div[data-testid="stButton"] button { border-radius: 8px !important; height: 40px !important; font-size: 16px !important; font-weight: 600 !important; transition: all 0.3s ease; }
    div[data-testid="stButton"] button[kind="primary"] { background-color: #00CC96 !important; border: none !important; color: #000 !important; box-shadow: 0 2px 5px rgba(0,204,150,0.3); }
    div[data-testid="stButton"] button[kind="primary"]:hover { background-color: #00A87D !important; }
    div[data-testid="stButton"] button[kind="secondary"] { background-color: transparent !important; border: 1px solid #666 !important; color: #CCC !important; }
    div[data-testid="stButton"] button[kind="secondary"]:hover { border-color: #FF5252 !important; color: #FF5252 !important; background-color: rgba(255, 82, 82, 0.1) !important; }
    .report-card { background-color: #1E1E1E; border: 1px solid #444; border-radius: 10px; padding: 15px; margin-bottom: 15px; }
    [data-testid="stDataFrame"] { background-color: #262730; }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

if "pending_select_all" not in st.session_state: st.session_state.pending_select_all = False
if "working_select_all" not in st.session_state: st.session_state.working_select_all = False

try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']
completed = [o for o in all_data if o.get('vendor_status') == '已回貨']

tab1, tab2, tab3 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})", f"📜 歷史紀錄"])

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
        st.write("")

        selected_p = []
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 9])
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}"):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")

        if selected_p:
            st.markdown(f"""<div style="background-color:#00332a; padding:10px; border-radius:8px; border:1px solid #00CC96; margin-top:15px; margin-bottom:10px;">
                <span style="color:#00CC96; font-weight:bold; font-size:16px;">📥 準備接收 {len(selected_p)} 筆工單</span>
            </div>""", unsafe_allow_html=True)
            
            v_name = st.text_input("請輸入領收人姓名", key="p_staff")
            if st.button("確認接收", type="primary", key="p_confirm"):
                if v_name:
                    for wo in selected_p:
                        supabase.table("vendor_orders").update({"vendor_status": "加工中", "vendor_staff": v_name}).eq("work_order", wo).execute()
                        
                        # 【LINE 通知】
                        current_wo = next((x['customer_wo'] for x in pending if x['work_order'] == wo), "未知工單")
                        msg = f"🔔 廠商已接收工單\n📄 工單：{current_wo}\n👤 領收人：{v_name}"
                        send_line_msg(msg)

                    st.success("接收成功！LINE 通知已發送")
                    st.rerun()
                else: st.warning("請填寫姓名")

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
        st.write("")

        selected_w_data = []
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1, 9])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w_data.append(o)
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 發單數：{o.get('order_qty')}")

        if selected_w_data:
            st.markdown(f"""<div style="background-color:#3e2723; padding:10px; border-radius:8px; border:1px solid #FFAB91; margin-top:20px; margin-bottom:20px;">
                <span style="color:#FFAB91; font-weight:bold; font-size:16px;">🚀 正在填寫 {len(selected_w_data)} 筆回報資料</span>
            </div>""", unsafe_allow_html=True)
            
            for item in selected_w_data:
                wo_id = item['work_order']
                qty = item['order_qty']
                with st.container():
                    st.markdown(f"""<div class="report-card"><h4 style="color:#00FFCC!important; margin:0;">📄 {item['customer_wo']}</h4>
                        <p style="margin:0; font-size:14px; color:#AAA;">機種：{item['customer_model']} | <b>總數：{qty}</b></p></div>""", unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 2])
                    ng_val = c1.number_input("❌ NG 數量", min_value=0, max_value=qty, value=0, key=f"ng_in_{wo_id}")
                    rem_val = c2.text_input("📝 備註", key=f"rem_in_{wo_id}")
                    st.caption(f"✅ 自動計算良品 (OK)： **{qty - ng_val}**")
                    st.divider()

            st.markdown("### 👤 確認送出")
            vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
            if st.button("確認完工送出", type="primary", key="w_confirm"):
                if vw_name:
                    for item in selected_w_data:
                        wo_id = item['work_order']
                        qty = item['order_qty']
                        final_ng = st.session_state[f"ng_in_{wo_id}"]
                        final_rem = st.session_state[f"rem_in_{wo_id}"]
                        supabase.table("vendor_orders").update({
                            "vendor_status": "已回貨", "vendor_staff": vw_name,
                            "return_qty": qty, "ok_qty": qty - final_ng, "ng_qty": final_ng,
                            "vendor_remark": final_rem, "return_time": datetime.now().isoformat()
                        }).eq("work_order", wo_id).execute()
                        
                        # 【LINE 通知】
                        msg = f"🚀 廠商已回報完工\n📄 工單：{item['customer_wo']}\n✅ 良品：{qty - final_ng}\n❌ NG：{final_ng}\n👤 經手人：{vw_name}"
                        if final_rem: msg += f"\n📝 備註：{final_rem}"
                        send_line_msg(msg)

                    st.success("回報成功！LINE 通知已發送")
                    st.rerun()
                else: st.warning("請填寫姓名")

with tab3:
    st.markdown("### 🔍 完工履歷查詢")
    search_q = st.text_input("輸入工單號碼或機種搜尋...", key="hist_search")
    if completed:
        df = pd.DataFrame(completed)
        if search_q:
            df = df[df['customer_wo'].astype(str).str.contains(search_q, case=False) | df['customer_model'].astype(str).str.contains(search_q, case=False)]
        if not df.empty:
            df["return_time"] = df["return_time"].apply(lambda x: x[:16].replace('T', ' ') if x else '-')
            df_show = df[["return_time", "customer_wo", "customer_model", "ok_qty", "ng_qty", "vendor_staff", "vendor_remark"]].copy()
            df_show.columns = ["時間", "工單", "機種", "OK", "NG", "經手人", "備註"]
            st.dataframe(df_show, use_container_width=True, hide_index=True)
        else: st.warning("查無資料")
    else: st.info("尚無歷史紀錄")

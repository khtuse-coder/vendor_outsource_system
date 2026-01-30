import streamlit as st
from supabase import create_client
from datetime import datetime
import pandas as pd

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

# 【深色高對比主題】
st.markdown("""
    <style>
    /* 深色背景 */
    .stApp { background-color: #0E1117 !important; }
    
    /* 文字顏色 */
    h1, h2, h3, h4, p, label, div { color: #FAFAFA !important; }
    h1 { font-size: 26px !important; font-weight: 800 !important; color: #00FFCC !important; }
    
    /* 勾選框放大 */
    [data-testid="stCheckbox"] { transform: scale(1.5); margin-right: 10px; }
    
    /* 輸入框優化 */
    .stNumberInput input { font-size: 20px !important; font-weight: bold; min-height: 50px; }
    .stTextInput input { min-height: 50px; }
    
    /* 表格樣式優化 (針對歷史紀錄) */
    [data-testid="stDataFrame"] { background-color: #262730 !important; border: 1px solid #444; border-radius: 5px; }
    
    /* 卡片樣式 */
    .report-card {
        background-color: #1E1E1E; border: 1px solid #444; border-radius: 10px; padding: 15px; margin-bottom: 15px;
    }
    
    /* 按鈕樣式 */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00CC96 !important; border: none !important; color: #000 !important; 
        font-weight: bold !important; height: 3em !important; font-size: 18px !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #262730 !important; border: 1px solid #4F4F4F !important; color: #FFF !important;
        height: 3em !important; font-size: 18px !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📦 廠商端加工系統")

# Session State
if "pending_select_all" not in st.session_state: st.session_state.pending_select_all = False
if "working_select_all" not in st.session_state: st.session_state.working_select_all = False

# 抓取資料
try:
    res = supabase.table("vendor_orders").select("*").order("send_time", desc=True).execute()
    all_data = res.data
except:
    all_data = []

pending = [o for o in all_data if o.get('vendor_status') == '待接收']
working = [o for o in all_data if o.get('vendor_status') == '加工中']
# 篩選出已完工的歷史資料
completed = [o for o in all_data if o.get('vendor_status') == '已回貨']

# 增加第三個分頁：歷史紀錄
tab1, tab2, tab3 = st.tabs([
    f"🆕 待接收 ({len(pending)})", 
    f"⚙️ 加工中 ({len(working)})", 
    f"📜 歷史紀錄"
])

# --- Tab 1: 待接收 ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        c_btn1, c_btn2, _ = st.columns([1, 1, 1])
        if c_btn1.button("✅ 全選", key="p_all", type="primary"):
            for o in pending: st.session_state[f"p_ck_{o['work_order']}"] = True
            st.rerun()
        if c_btn2.button("❌ 取消", key="p_none", type="secondary"):
            for o in pending: st.session_state[f"p_ck_{o['work_order']}"] = False
            st.rerun()
        st.write("---")

        selected_p = []
        for o in pending:
            with st.container(border=True):
                c_sel, c_info = st.columns([1.5, 8.5])
                if c_sel.checkbox("", key=f"p_ck_{o['work_order']}"):
                    selected_p.append(o['work_order'])
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 數量：{o.get('order_qty')}")

        if selected_p:
            st.markdown(f"""<div style="background-color:#004D40;padding:10px;border-radius:10px;border:1px solid #00CC96;margin-top:10px;">
                <h3 style="margin:0;color:#00FFCC!important;">📥 準備接收 {len(selected_p)} 筆</h3>
            </div>""", unsafe_allow_html=True)
            v_name = st.text_input("請輸入領收人姓名", key="p_staff")
            if st.button("確認接收", type="primary", key="p_confirm"):
                if v_name:
                    for wo in selected_p:
                        supabase.table("vendor_orders").update({"vendor_status": "加工中", "vendor_staff": v_name}).eq("work_order", wo).execute()
                    st.rerun()
                else: st.warning("請填寫姓名")

# --- Tab 2: 加工中 (手機大卡片版) ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        w_btn1, w_btn2, _ = st.columns([1, 1, 1])
        if w_btn1.button("✅ 全選", key="w_all", type="primary"): 
            for o in working: st.session_state[f"w_ck_{o['work_order']}"] = True
            st.rerun()
        if w_btn2.button("❌ 取消", key="w_none", type="secondary"): 
            for o in working: st.session_state[f"w_ck_{o['work_order']}"] = False
            st.rerun()
        st.write("---")

        selected_w_data = []
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1.5, 8.5])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w_data.append(o)
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 發單數：{o.get('order_qty')}")

        if selected_w_data:
            st.markdown(f"""<div style="background-color:#5D4037;padding:10px;border-radius:10px;border:1px solid #FFAB91;margin-top:20px;margin-bottom:20px;">
                <h3 style="margin:0;color:#FFAB91!important;">🚀 填寫詳細資料 ({len(selected_w_data)} 筆)</h3>
            </div>""", unsafe_allow_html=True)
            
            for item in selected_w_data:
                wo_id = item['work_order']
                qty = item['order_qty']
                with st.container():
                    st.markdown(f"""
                    <div class="report-card">
                        <h3 style="color:#00FFCC!important;">📄 工單：{item['customer_wo']}</h3>
                        <p style="color:#CCC;">機種：{item['customer_model']} | <b>總數：{qty}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
                    c1, c2 = st.columns([1, 2])
                    ng_val = c1.number_input("❌ NG 數量", min_value=0, max_value=qty, value=0, key=f"ng_in_{wo_id}")
                    rem_val = c2.text_input("📝 備註", key=f"rem_in_{wo_id}")
                    st.caption(f"✅ 良品數： **{qty - ng_val}**")
                    st.divider()

            st.markdown("### 👤 最後確認")
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
                            "return_qty": qty, "ok_qty": qty - final_ng, "ng_qty": final_ng,
                            "vendor_remark": final_rem, "return_time": datetime.now().isoformat()
                        }).eq("work_order", wo_id).execute()
                    st.success("回報成功！")
                    st.rerun()
                else: st.warning("請填寫姓名")

# --- Tab 3: 歷史紀錄 (履歷查詢) ---
with tab3:
    st.markdown("### 🔍 完工履歷查詢")
    
    # 搜尋框
    search_q = st.text_input("輸入工單號碼或機種搜尋...", key="hist_search")
    
    if not completed:
        st.info("尚無歷史紀錄")
    else:
        # 轉換資料為 DataFrame
        df = pd.DataFrame(completed)
        
        # 篩選功能
        if search_q:
            df = df[df['customer_wo'].astype(str).str.contains(search_q, case=False) | 
                    df['customer_model'].astype(str).str.contains(search_q, case=False)]
        
        if not df.empty:
            # 整理要顯示的欄位與名稱 (中文化)
            # 處理時間格式，只留日期與時間到分
            df["return_time"] = df["return_time"].apply(lambda x: x[:16].replace('T', ' ') if x else '-')
            
            df_show = df[["return_time", "customer_wo", "customer_model", "return_qty", "ng_qty", "vendor_staff", "vendor_remark"]].copy()
            df_show.columns = ["完工時間", "工單", "機種", "交貨數", "NG數", "經手人", "備註"]
            
            # 顯示表格 (可排序)
            st.dataframe(
                df_show, 
                use_container_width=True, 
                hide_index=True,
                height=500 # 固定高度讓滑動更順
            )
        else:
            st.warning("查無符合資料")

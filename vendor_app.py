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

# 【視覺修復】CSS 精準化，不再誤殺表格
st.markdown("""
    <style>
    /* 1. 背景深色 */
    .stApp { background-color: #0E1117 !important; }
    
    /* 2. 只針對文字標籤變白，不影響表格內部的結構 */
    h1, h2, h3, h4, p, label, .stMarkdown { color: #FAFAFA !important; }
    
    /* 標題樣式 */
    h1 { font-size: 28px !important; font-weight: 800 !important; color: #00FFCC !important; }
    h3 { font-size: 22px !important; font-weight: bold !important; margin-bottom: 5px !important; }
    
    /* 勾選框放大 */
    [data-testid="stCheckbox"] { transform: scale(1.4); margin-left: 5px; }
    
    /* 3. 【關鍵修復】強制表格背景為深色，文字為淺色 */
    [data-testid="stDataFrame"] {
        background-color: #262730 !important;
        border: 1px solid #4F4F4F !important;
        border-radius: 5px;
    }
    /* 修正表格內文字顏色，避免白底白字 */
    div[data-testid="stDataFrame"] div[role="grid"] {
        color: #FAFAFA !important;
        background-color: #262730 !important;
    }

    /* 按鈕樣式 */
    div[data-testid="stButton"] button[kind="primary"] {
        background-color: #00CC96 !important; border: none !important; color: #000 !important; font-weight: bold !important;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background-color: #262730 !important; border: 1px solid #4F4F4F !important; color: #FFF !important;
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

tab1, tab2 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})"])

# --- Tab 1: 待接收 ---
with tab1:
    if not pending:
        st.info("目前無新工單")
    else:
        c_btn1, c_btn2, _ = st.columns([1, 1, 2])
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
                c_sel, c_info = st.columns([1, 8])
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

# --- Tab 2: 加工中 (表格修復版) ---
with tab2:
    if not working:
        st.info("目前無加工中工單")
    else:
        w_btn1, w_btn2, _ = st.columns([1, 1, 2])
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
                c_sel, c_info = st.columns([1, 8])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w_data.append(o)
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 發單數：{o.get('order_qty')}")

        if selected_w_data:
            st.markdown(f"""<div style="background-color:#5D4037;padding:10px;border-radius:10px;border:1px solid #FFAB91;margin-top:10px;margin-bottom:10px;">
                <h3 style="margin:0;color:#FFAB91!important;">🚀 填寫回報資訊 ({len(selected_w_data)} 筆)</h3>
            </div>""", unsafe_allow_html=True)
            
            # 建立資料表
            df = pd.DataFrame(selected_w_data)
            df["OK數"] = df["order_qty"]
            df["NG數"] = 0
            df["廠商備註"] = "" 
            
            # 使用 data_editor
            # 這裡不使用 st.write，直接用 st.data_editor 讓使用者編輯
            edited_data = st.data_editor(
                df,
                column_config={
                    "work_order": None, # 隱藏 ID
                    "customer_wo": st.column_config.TextColumn("工單", disabled=True),
                    "customer_model": st.column_config.TextColumn("機種", disabled=True),
                    "order_qty": st.column_config.NumberColumn("發單", disabled=True),
                    "OK數": st.column_config.NumberColumn("✅ OK", required=True, min_value=0),
                    "NG數": st.column_config.NumberColumn("❌ NG", required=True, min_value=0),
                    "廠商備註": st.column_config.TextColumn("📝 備註", width="large"),
                },
                column_order=("customer_wo", "customer_model", "order_qty", "OK數", "NG數", "廠商備註", "work_order"),
                hide_index=True,
                use_container_width=True,
                key="editor_table"
            )
            
            vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
            
            if st.button("確認完工送出", type="primary", key="w_confirm"):
                if vw_name:
                    for index, row in edited_data.iterrows():
                        # 計算回貨總數
                        final_ret = row["OK數"] + row["NG數"]
                        
                        supabase.table("vendor_orders").update({
                            "vendor_status": "已回貨",
                            "vendor_staff": vw_name,
                            "return_qty": final_ret,
                            "ok_qty": row["OK數"],
                            "ng_qty": row["NG數"],
                            "vendor_remark": row["廠商備註"],
                            "return_time": datetime.now().isoformat()
                        }).eq("work_order", row["work_order"]).execute()
                    st.success("回報成功！")
                    st.rerun()
                else: st.warning("請填寫姓名")

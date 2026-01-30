import streamlit as st
from supabase import create_client
from datetime import datetime

# --- 1. 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- 2. 網頁頁面配置 ---
st.set_page_config(page_title="廠商加工回報", layout="centered")

# 【視覺重構】手機友善深色主題
st.markdown("""
    <style>
    /* 深色背景 */
    .stApp { background-color: #0E1117 !important; }
    
    /* 文字顏色 */
    h1, h2, h3, h4, p, label, div { color: #FAFAFA !important; }
    h1 { font-size: 26px !important; font-weight: 800 !important; color: #00FFCC !important; }
    
    /* 加大勾選框 */
    [data-testid="stCheckbox"] { transform: scale(1.5); margin-right: 10px; }
    
    /* 輸入框優化 (針對手機好點選) */
    .stNumberInput input { font-size: 20px !important; font-weight: bold; min-height: 50px; }
    .stTextInput input { min-height: 50px; }
    
    /* 讓卡片有點區隔 */
    .report-card {
        background-color: #1E1E1E;
        border: 1px solid #444;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
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

tab1, tab2 = st.tabs([f"🆕 待接收 ({len(pending)})", f"⚙️ 加工中 ({len(working)})"])

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

# --- Tab 2: 加工中 (【手機優化】卡片式輸入) ---
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
        # 1. 勾選區
        for o in working:
            with st.container(border=True):
                c_sel, c_info = st.columns([1.5, 8.5])
                if c_sel.checkbox("", key=f"w_ck_{o['work_order']}"):
                    selected_w_data.append(o)
                with c_info:
                    st.markdown(f"### 📄 {o.get('customer_wo')}")
                    st.write(f"機種：{o.get('customer_model')} | 發單數：{o.get('order_qty')}")

        # 2. 填寫區 (改成卡片式，不用表格)
        if selected_w_data:
            st.markdown(f"""<div style="background-color:#5D4037;padding:10px;border-radius:10px;border:1px solid #FFAB91;margin-top:20px;margin-bottom:20px;">
                <h3 style="margin:0;color:#FFAB91!important;">🚀 填寫詳細資料 ({len(selected_w_data)} 筆)</h3>
            </div>""", unsafe_allow_html=True)
            
            # 遍歷每一個勾選的項目，生成輸入卡片
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
                    # NG 輸入框：大大的數字輸入
                    ng_val = c1.number_input("❌ NG 數量", min_value=0, max_value=qty, value=0, key=f"ng_in_{wo_id}")
                    # 備註輸入框
                    rem_val = c2.text_input("📝 備註 (選填)", key=f"rem_in_{wo_id}")
                    
                    # 顯示自動計算的 OK 數量
                    ok_calc = qty - ng_val
                    st.caption(f"✅ 自動計算良品 (OK) 數量： **{ok_calc}**")
                    st.divider()

            # 底部送出區
            st.markdown("### 👤 最後確認")
            vw_name = st.text_input("請輸入回報人姓名", key="w_staff")
            
            if st.button("確認完工送出", type="primary", key="w_confirm"):
                if vw_name:
                    for item in selected_w_data:
                        wo_id = item['work_order']
                        qty = item['order_qty']
                        
                        # 從 session_state 抓取剛剛填的值
                        final_ng = st.session_state[f"ng_in_{wo_id}"]
                        final_rem = st.session_state[f"rem_in_{wo_id}"]
                        final_ok = qty - final_ng
                        
                        supabase.table("vendor_orders").update({
                            "vendor_status": "已回貨",
                            "vendor_staff": vw_name,
                            "return_qty": qty, # 總回貨數
                            "ok_qty": final_ok,
                            "ng_qty": final_ng,
                            "vendor_remark": final_rem,
                            "return_time": datetime.now().isoformat()
                        }).eq("work_order", wo_id).execute()
                    st.success("回報成功！")
                    st.rerun()
                else: st.warning("請填寫姓名")

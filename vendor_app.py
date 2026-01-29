import sqlite3
from supabase import create_client
import os

# --- 連線設定 ---
SUPABASE_URL = "https://iomqohzyuwtbfxnoavjf.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlvbXFvaHp5dXd0YmZ4bm9hdmpmIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Njk2NTUxMzUsImV4cCI6MjA4NTIzMTEzNX0.raqhaFGXC50xWODruMD0M26HgDq0XC74KaOe48UpXP8"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

DB_PATH = r"\\10.84.53.117\blc\mfg\物料區用\liteon.db"

def sync():
    if not os.path.exists(DB_PATH):
        print("❌ 找不到資料庫檔案！")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 這裡要確保抓取的順序跟下面 payload 對得上
    query = "SELECT Work_Order, Customer_WO, Customer_Model, WorkOrder_Qty, Create_Time FROM Material_WorkOrder_Info WHERE Status = 'OUTSOURCE'"
    cursor.execute(query)
    rows = cursor.fetchall()

    print(f"📡 找到 {len(rows)} 筆 OUTSOURCE 資料...")

    for row in rows:
        # 印出來檢查抓到的內容
        print(f"🔍 準備同步：工單={row[1]}, 機種={row[2]}, 數量={row[3]}")
        
        payload = {
            "work_order": row[0],
            "customer_wo": str(row[1]) if row[1] else "無資料", # 確保不是空值
            "customer_model": str(row[2]) if row[2] else "無資料",
            "order_qty": int(row[3]),
            "send_time": str(row[4]),
            "vendor_status": "待接收"
        }
        
        try:
            supabase.table("vendor_orders").upsert(payload, on_conflict="work_order").execute()
            print(f"✅ {row[1]} 同步成功")
        except Exception as e:
            print(f"❌ {row[1]} 同步失敗：{e}")

    conn.close()

if __name__ == "__main__":
    sync()

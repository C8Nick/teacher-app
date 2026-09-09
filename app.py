import streamlit as st
import requests
import datetime
import pandas as pd
from PIL import Image
import base64
import io

# ❗❗❗ 你的 Google Apps Script 網址 ❗❗❗
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyR1yso10uCean3ZpwjFkzWaLfLU51b9hJj5PCcSQzS8flZPcp4o8DIuo1PHQIFWLpq/exec"

# ================= 頁面設定 =================
# 讀取你的 LOGO 圖片
img_icon = Image.open("LOGO.png")

# 將 page_icon 換成你的 LOGO 圖片變數
st.set_page_config(page_title="奇幻島教師服務系統", page_icon=img_icon, layout="centered")

# 初始化 Session State (用來記住登入狀態與資料)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "profile_data" not in st.session_state:
    st.session_state.profile_data = []

# ================= 登入頁面 =================
if not st.session_state.logged_in:
    
    col1, col2, col3 = st.columns([0.5, 1, 0.5])
    with col2:
        st.image("LOGO.png", use_container_width=True)
        
    st.markdown("<h2 style='text-align: center;'>奇幻島教師服務系統</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>歡迎回來，請登入您的帳號</p>", unsafe_allow_html=True)
    
    with st.container():
        acc = st.text_input("帳號 (手機)")
        pwd = st.text_input("密碼", type="password")
        
        if st.button("登入", use_container_width=True, type="primary"):
            if not acc or not pwd:
                st.warning("請輸入帳號與密碼！")
            elif pwd != "123456":
                st.error("密碼錯誤！")
            else:
                with st.spinner("載入資料中，請稍候..."):
                    try:
                        res = requests.get(WEB_APP_URL, params={"action": "get_profile", "account": acc})
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.profile_data = data if data else [acc] + [""]*11
                            st.session_state.current_user = acc
                            st.session_state.logged_in = True
                            st.rerun() # 重新整理頁面進入主系統
                        else:
                            st.error("連線錯誤，請確認網址")
                    except Exception as e:
                        st.error(f"無法連線到伺服器: {e}")

# ================= 主系統頁面 =================
else:
    col1, col2 = st.columns([1, 5])
    
    with col1:
        st.image("LOGO.png", use_container_width=True)
        
    with col2:
        st.title("奇幻島教師服務系統")

    if st.sidebar.button("登出", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state.profile_data = []
        st.rerun()

    # 🌟 取出老師名稱
    p_data = st.session_state.profile_data
    if len(p_data) > 3 and str(p_data[3]).strip():
        teacher_name = str(p_data[3]).strip()
    elif len(p_data) > 1 and str(p_data[1]).strip():
        teacher_name = str(p_data[1]).strip()
    else:
        teacher_name = st.session_state.current_user
        
    st.sidebar.success(f"歡迎, {teacher_name}")

    # 🌟 這裡修改了 Tab 的名稱：將「借還」改為「請款」
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ 回報", "🧾 請款", "💰 結算", "👤 個人"])

    # === 第一頁：回報 ===
    with tab1:
        st.link_button("📅 課程行事曆訂閱", "", use_container_width=True)
        st.subheader("填寫課後回報")
        
        with st.form("report_form"):
            job = st.selectbox("職位", ["老師", "助教"])
            date = st.date_input("課程日期", datetime.date.today())
            
            col1, col2 = st.columns(2)
            with col1: start_t = st.time_input("上課時間", datetime.time(14, 0))
            with col2: end_t = st.time_input("下課時間", datetime.time(16, 0))
            
            branch = st.text_input("班部名稱")
            hours = st.number_input("上課時數 (小時)", min_value=0.0, value=2.0, step=0.5)
            content = st.text_area("課程內容與特殊狀況")
            
            if st.form_submit_button("送出回報", type="primary", use_container_width=True):
                if not branch:
                    st.warning("請填寫班部名稱！")
                else:
                    taiwan_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                    timestamp = taiwan_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    row_data = [timestamp, date.strftime("%Y/%m/%d"), teacher_name, start_t.strftime("%H:%M"), end_t.strftime("%H:%M"), branch, hours, content, job]
                    try:
                        requests.post(WEB_APP_URL, json={"sheet_name": "回報", "row": row_data})
                        st.success("課程回報已送出！")
                    except Exception as e:
                        st.error("連線失敗")

  # === 第二頁：請款 (全新修改為動態表格) ===
    with tab2:
        st.subheader("🧾 申請請款")
        
        # 初始化請款表格的 Session State
        if "claim_df" not in st.session_state:
            st.session_state.claim_df = pd.DataFrame([{"物品 / 請款項目名稱": "", "金額 (元)": 0}])
            
        st.write("請填寫請款項目（可點擊表格下方 ➕ 新增列）：")
        
        # 使用 data_editor 產生可編輯與新增的動態表格
        edited_claim_df = st.data_editor(
            st.session_state.claim_df, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "金額 (元)": st.column_config.NumberColumn("金額 (元)", min_value=0, step=1)
            }
        )
        
        st.markdown("##### 📸 上傳收據或發票")
        st.info("💡 手機操作時，點擊下方按鈕可直接選擇「拍照」或「相簿」。")
        # 加上 key 確保送出後可以用 rerun 清空狀態
        receipt_file = st.file_uploader("請上傳照片", type=["jpg", "jpeg", "png"], key="claim_file")
        
        notes = st.text_area("備註說明 (選填)", key="claim_notes")
        
        if st.button("送出請款申請", type="primary", use_container_width=True):
            # 過濾掉沒有填寫物品名稱的空白列
            valid_claims = edited_claim_df[edited_claim_df["物品 / 請款項目名稱"].str.strip() != ""]
            
            if valid_claims.empty:
                st.warning("請至少填寫一項請款物品！")
            elif valid_claims["金額 (元)"].sum() <= 0:
                st.warning("請款總金額必須大於 0！")
            elif not receipt_file:
                st.warning("請務必上傳或拍攝收據/發票照片！")
            else:
                with st.spinner("圖片處理與上傳中，請稍候..."):
                    try:
                        # 計算總金額
                        total_amount = int(valid_claims["金額 (元)"].sum())
                        
                        # 把品項跟價錢組合成字串，方便 Google Sheet 閱讀 (例如：文具 (100元) \n 影印 (50元))
                        item_details = "\n".join(
                            [f"{row['物品 / 請款項目名稱']} ({int(row['金額 (元)'])}元)" for _, row in valid_claims.iterrows()]
                        )
                        
                        # 1. 壓縮圖片
                        img = Image.open(receipt_file)
                        if img.mode != 'RGB':
                            img = img.convert('RGB')
                        
                        img.thumbnail((800, 800))
                        buffered = io.BytesIO()
                        img.save(buffered, format="JPEG", quality=75)
                        base64_img = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        
                        # 2. 組合送出的資料
                        taiwan_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                        timestamp = taiwan_time.strftime("%Y-%m-%d %H:%M:%S")
                        
                        # 寫入資料：時間, 老師名稱, 品項明細, 總金額, 備註, 圖片Base64
                        row_data = [timestamp, teacher_name, item_details, total_amount, notes, base64_img]
                        
                        res = requests.post(WEB_APP_URL, json={"sheet_name": "請款", "row": row_data})
                        
                        if res.status_code == 200:
                            st.success("🎉 請款申請已成功送出！")
                            # 送出成功後清空暫存表格
                            st.session_state.claim_df = pd.DataFrame([{"物品 / 請款項目名稱": "", "金額 (元)": 0}]) 
                            st.rerun() # 重新整理頁面，清空上傳圖片和備註的狀態
                        else:
                            st.error("伺服器錯誤，請稍後再試。")
                    except Exception as e:
                        st.error(f"處理失敗: {e}")

    # === 第三頁：結算 ===
    with tab3:
        st.subheader("薪資結算申請")
        
        current_year = datetime.datetime.now().year
        months = [f"{current_year}/{i:02d}" for i in range(1, 13)]
        selected_month = st.selectbox("選擇結算月份", months, index=datetime.datetime.now().month - 1)
        
        if st.button("🔍 查詢當月回報資料", use_container_width=True):
            with st.spinner("查詢中..."):
                try:
                    res = requests.get(WEB_APP_URL, params={"action": "get_summary", "teacher": teacher_name, "month": selected_month})
                    if res.status_code == 200:
                        data = res.json()
                        st.session_state.settle_data = data
                    else:
                        st.error("無法獲取資料")
                except Exception as e:
                    st.error("連線失敗")
                    
        if "settle_data" in st.session_state:
            data = st.session_state.settle_data
            if data:
                df = pd.DataFrame(data)
                df = df.rename(columns={
                    "branch": "班部名稱", 
                    "teacher_hours": "老師總時數", 
                    "ta_hours": "助教總時數"
                })
                st.dataframe(df, use_container_width=True, hide_index=True)
                
                total_teacher_hours = sum([float(item["teacher_hours"]) for item in data])
                total_ta_hours = sum([float(item["ta_hours"]) for item in data])
                
                total_str = f"老師總計：{total_teacher_hours} 小時 ｜ 助教總計：{total_ta_hours} 小時"
                st.markdown(f"#### {total_str}")
                
                if st.button("提交結算申請", type="primary", use_container_width=True):
                    taiwan_time = datetime.datetime.utcnow() + datetime.timedelta(hours=8)
                    timestamp = taiwan_time.strftime("%Y-%m-%d %H:%M:%S")
                    
                    p_data = st.session_state.profile_data
                    bank_code = str(p_data[10]).replace("None","") if len(p_data) > 10 else ""
                    bank_acc = str(p_data[11]).replace("None","") if len(p_data) > 11 else ""
                    
                    try:
                        requests.post(WEB_APP_URL, json={
                            "sheet_name": "結算", 
                            "row": [timestamp, teacher_name, selected_month, bank_code, bank_acc, total_teacher_hours, total_ta_hours]
                        })
                        st.success("結算申請已提交！")
                    except Exception as e:
                        st.error("連線失敗")
            else:
                st.info("這個月沒有您的回報紀錄喔！")

    # === 第四頁：個人 ===
    with tab4:
        st.subheader("基本資訊")
        p_data = st.session_state.profile_data
        
        while len(p_data) < 12: p_data.append("")
        def clean(val): return str(val).replace("T16:00:00.000Z", "").replace("None", "") if val else ""

        with st.form("profile_form"):
            name = st.text_input("姓名", value=clean(p_data[1]))
            id_num = st.text_input("身份證字號", value=clean(p_data[2]))
            nickname = st.text_input("老師(綽號)", value=clean(p_data[3]))
            birthday = st.text_input("生日 (YYYY/MM/DD)", value=clean(p_data[4]))
            email = st.text_input("電子郵件", value=clean(p_data[5]))
            line_id = st.text_input("LINE ID", value=clean(p_data[6]))
            phone = st.text_input("緊急聯絡人", value=clean(p_data[7]))
            hometown = st.text_input("戶籍地址", value=clean(p_data[8]))
            address = st.text_input("居住地址", value=clean(p_data[9]))
            
            st.markdown("##### 💳 撥款銀行帳戶")
            bank_code = st.text_input("銀行代碼", value=clean(p_data[10]))
            bank_acc = st.text_input("銀行帳號", value=clean(p_data[11]))
            
            if st.form_submit_button("儲存資料", type="primary", use_container_width=True):
                row_data = [st.session_state.current_user, name, id_num, nickname, birthday, email, line_id, phone, hometown, address, bank_code, bank_acc]
                try:
                    requests.post(WEB_APP_URL, json={"sheet_name": "個人資訊", "row": row_data})
                    st.session_state.profile_data = row_data 
                    st.success("個人資料已儲存！")
                    st.rerun() 
                except Exception as e:
                    st.error("連線失敗")

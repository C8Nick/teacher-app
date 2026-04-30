import streamlit as st
import requests
import datetime
import pandas as pd

# ❗❗❗ 你的 Google Apps Script 網址 ❗❗❗
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbwZUNzKxJO-saVs7hjoAXTGoRkxV2j8lgmDwse9umZk1OhUBMfO88kASDfz-H57H9Y3/exec"

# ================= 頁面設定 =================
st.set_page_config(page_title="教師服務系統", page_icon="👩‍🏫", layout="centered")

# 初始化 Session State (用來記住登入狀態與資料)
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = ""
if "profile_data" not in st.session_state:
    st.session_state.profile_data = []

# ================= 登入頁面 =================
if not st.session_state.logged_in:
    st.markdown("<h2 style='text-align: center;'>👩‍🏫 教師服務系統</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>歡迎回來，請登入您的帳號</p>", unsafe_allow_html=True)
    
    with st.container():
        acc = st.text_input("帳號 (手機或 Email)")
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
    st.title("👩‍🏫 教師服務系統")
    
    # 登出按鈕
    if st.sidebar.button("登出", type="secondary"):
        st.session_state.logged_in = False
        st.session_state.current_user = ""
        st.session_state.profile_data = []
        st.rerun()

    # 取出老師名稱 (如果個人資料有填的話)
    teacher_name = st.session_state.profile_data[1] if len(st.session_state.profile_data) > 1 and st.session_state.profile_data[1] else st.session_state.current_user
    st.sidebar.success(f"歡迎, {teacher_name}")

    # 使用 Tab 來做手機版友好的導覽列
    tab1, tab2, tab3, tab4 = st.tabs(["✍️ 回報", "📦 借還", "💰 結算", "👤 個人"])

    # === 第一頁：回報 ===
    with tab1:
        st.link_button("📅 課程行事曆訂閱", "https://docs.google.com/spreadsheets/d/1fJvp0Q2GPrXygX69M5AAy8QjiKGAJge01H-4kMo84xM/edit?usp=sharing", use_container_width=True)
        st.subheader("填寫課後回報")
        
        with st.form("report_form"):
            job = st.selectbox("職位", ["老師", "助教"])
            date = st.date_input("課程日期", datetime.date.today())
            
            col1, col2 = st.columns(2)
            with col1: start_t = st.time_input("上課時間", datetime.time(14, 0))
            with col2: end_t = st.time_input("下課時間", datetime.time(16, 0))
            
            branch = st.text_input("班部名稱")
            hours = st.number_input("上課時數 (小時)", min_value=0.0, value=2.0, step=0.5)
            content = st.text_area("課程進度與備註")
            
            if st.form_submit_button("送出回報", type="primary", use_container_width=True):
                if not branch:
                    st.warning("請填寫班部名稱！")
                else:
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_data = [timestamp, date.strftime("%Y/%m/%d"), teacher_name, start_t.strftime("%H:%M"), end_t.strftime("%H:%M"), branch, hours, content, job]
                    try:
                        requests.post(WEB_APP_URL, json={"sheet_name": "回報", "row": row_data})
                        st.success("課程回報已送出！")
                    except:
                        st.error("連線失敗")

    # === 第二頁：借還 ===
    with tab2:
        st.subheader("申請借用工具")
        
        # Streamlit 超強的動態表格編輯器
        if "borrow_df" not in st.session_state:
            st.session_state.borrow_df = pd.DataFrame([{"物品名稱": "", "數量": 1}])
            
        st.write("請填寫欲借用的物品（可點擊表格下方新增列）：")
        edited_df = st.data_editor(st.session_state.borrow_df, num_rows="dynamic", use_container_width=True)
        notes = st.text_area("備註")
        
        if st.button("送出借用申請", type="primary", use_container_width=True):
            # 過濾掉沒有填寫物品名稱的空白列
            valid_items = edited_df[edited_df["物品名稱"].str.strip() != ""]
            if valid_items.empty:
                st.warning("請至少填寫一項物品！")
            else:
                names = "\n".join(valid_items["物品名稱"].astype(str).tolist())
                qtys = "\n".join(valid_items["數量"].astype(str).tolist())
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                row_data = [timestamp, teacher_name, names, qtys, notes]
                try:
                    requests.post(WEB_APP_URL, json={"sheet_name": "借還", "row": row_data})
                    st.success("借用申請已送出！")
                    st.session_state.borrow_df = pd.DataFrame([{"物品名稱": "", "數量": 1}]) # 清空表格
                    st.rerun()
                except:
                    st.error("連線失敗")

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
                except:
                    st.error("連線失敗")
                    
        # 如果有查詢到資料，顯示表格與提交按鈕
        if "settle_data" in st.session_state:
            data = st.session_state.settle_data
            if data:
                df = pd.DataFrame(data)
                df.columns = ["班部名稱", "總時數"]
                st.dataframe(df, use_container_width=True, hide_index=True)
                total_hours = sum([float(item["hours"]) for item in data])
                total_str = f"總計時數：{total_hours} 小時"
                st.markdown(f"#### {total_str}")
                
                if st.button("提交結算申請", type="primary", use_container_width=True):
                    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # 從個人資料中抓取銀行帳號
                    p_data = st.session_state.profile_data
                    bank_code = str(p_data[10]).replace("None","") if len(p_data) > 10 else ""
                    bank_acc = str(p_data[11]).replace("None","") if len(p_data) > 11 else ""
                    
                    try:
                        requests.post(WEB_APP_URL, json={
                            "sheet_name": "結算", 
                            "row": [timestamp, teacher_name, selected_month, bank_code, bank_acc, total_str]
                        })
                        st.success("結算申請已提交！")
                    except:
                        st.error("連線失敗")
            else:
                st.info("這個月沒有您的回報紀錄喔！")

    # === 第四頁：個人 ===
    with tab4:
        st.subheader("基本資訊")
        p_data = st.session_state.profile_data
        
        # 幫空陣列補齊長度，避免 list index out of range
        while len(p_data) < 12: p_data.append("")
        def clean(val): return str(val).replace("T16:00:00.000Z", "").replace("None", "") if val else ""

        with st.form("profile_form"):
            name = st.text_input("姓名", value=clean(p_data[1]))
            id_num = st.text_input("身份證字號", value=clean(p_data[2]))
            nickname = st.text_input("老師(綽號)", value=clean(p_data[3]))
            birthday = st.text_input("生日 (YYYY/MM/DD)", value=clean(p_data[4]))
            email = st.text_input("電子郵件", value=clean(p_data[5]))
            line_id = st.text_input("LINE ID", value=clean(p_data[6]))
            phone = st.text_input("聯繫電話", value=clean(p_data[7]))
            hometown = st.text_input("戶籍地址", value=clean(p_data[8]))
            address = st.text_input("居住地址", value=clean(p_data[9]))
            
            st.markdown("##### 💳 撥款銀行帳戶")
            bank_code = st.text_input("銀行代碼", value=clean(p_data[10]))
            bank_acc = st.text_input("銀行帳號", value=clean(p_data[11]))
            
            if st.form_submit_button("儲存資料", type="primary", use_container_width=True):
                row_data = [st.session_state.current_user, name, id_num, nickname, birthday, email, line_id, phone, hometown, address, bank_code, bank_acc]
                try:
                    requests.post(WEB_APP_URL, json={"sheet_name": "個人資訊", "row": row_data})
                    st.session_state.profile_data = row_data # 更新本機暫存
                    st.success("個人資料已儲存！")
                    st.rerun() # 重新整理以更新側邊欄名稱
                except:
                    st.error("連線失敗")

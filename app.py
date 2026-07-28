import base64
from datetime import datetime
import io
import json
import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="ပ အမှတ် နှင့် အမှုတွဲ မှတ်တမ်းစနစ်",
    page_icon="🇲🇲",
    layout="wide",
)

# Initialize Database
def init_db():
    conn = sqlite3.connect("police_cases.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region TEXT,
            district TEXT,
            township TEXT,
            station TEXT,
            caseNo TEXT,
            crime TEXT,
            section TEXT,
            date TEXT,
            incidentDate TEXT,
            legalAdviceReqDate TEXT,
            legalAdviceRecDate TEXT,
            chargeDate TEXT,
            chargedSection TEXT,
            courtCaseInfo TEXT,
            officer TEXT,
            complainantName TEXT,
            accusedName TEXT,
            accusedStatus TEXT,
            parentsName TEXT,
            age TEXT,
            nrc TEXT,
            phone TEXT,
            address TEXT,
            marks TEXT,
            seizedItems TEXT,
            status TEXT,
            photo TEXT,
            details TEXT,
            isTrashed INTEGER DEFAULT 0
        )
    """)
    conn.commit()
    conn.close()

init_db()

def run_query(query, params=(), fetch=True):
    conn = sqlite3.connect("police_cases.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    conn.commit()
    result = cursor.fetchall() if fetch else None
    conn.close()
    return result

# Admin Authentication State
if "admin_auth" not in st.session_state:
    st.session_state.admin_auth = False
if "admin_pass" not in st.session_state:
    st.session_state.admin_pass = "admin123"

# Sidebar / Admin Panel
st.sidebar.title("🔐 စီမံခန့်ခွဲမှု (Admin Lock)")
admin_input = st.sidebar.text_input("Admin Password ရိုက်ထည့်ပါ", type="password")
if st.sidebar.button("Login ဝင်မည်"):
    if admin_input == st.session_state.admin_pass:
        st.session_state.admin_auth = True
        st.sidebar.success("Admin ဝင်ရောက်မှု အောင်မြင်ပါသည်။")
    else:
        st.sidebar.error("Password မှားယွင်းနေပါသည်။")

if st.session_state.admin_auth:
    st.sidebar.info("🔓 Admin ခွင့်ပြုချက် ရရှိထားပါသည်။")
    new_p = st.sidebar.text_input("Password အသစ်ပြောင်းရန်", type="password")
    if st.sidebar.button("Password ပြောင်းမည်") and len(new_p) >= 4:
        st.session_state.admin_pass = new_p
        st.sidebar.success("Password ပြောင်းလဲပြီးပါပြီ။")

# Main Title
st.markdown("<h2 style='text-align: center; color: #1a365d;'>🇲🇲 ပ အမှတ် နှင့် အမှုတွဲ မှတ်တမ်းစနစ် (Dashboard)</h2>", unsafe_allow_html=True)

# Fetch all data
data_rows = run_query("SELECT * FROM cases")
columns = [
    "id", "region", "district", "township", "station", "caseNo", "crime", "section",
    "date", "incidentDate", "legalAdviceReqDate", "legalAdviceRecDate", "chargeDate",
    "chargedSection", "courtCaseInfo", "officer", "complainantName", "accusedName",
    "accusedStatus", "parentsName", "age", "nrc", "phone", "address", "marks",
    "seizedItems", "status", "photo", "details", "isTrashed"
]
df = pd.DataFrame(data_rows, columns=columns) if data_rows else pd.DataFrame(columns=columns)

if not df.empty:
    active_df = df[df["isTrashed"] == 0]
    trash_df = df[df["isTrashed"] == 1]
else:
    active_df = df
    trash_df = df

# Statistics Cards
total_cases = len(active_df)
investigating_count = len(active_df[active_df["status"] == "စစ်ဆေးဆဲ"]) if not active_df.empty else 0
court_count = len(active_df[active_df["status"] == "တရားစွဲတင်"]) if not active_df.empty else 0
absconder_count = len(active_df[active_df["status"] == "တရားခံပြေး"]) if not active_df.empty else 0
closed_count = len(active_df[active_df["status"] == "ပြီးပြတ်/ပိတ်"]) if not active_df.empty else 0
trash_count = len(trash_df) if not trash_df.empty else 0

col1, col2, col3, col4, col5, col6 = st.columns(6)
col1.metric("စုစုပေါင်း", total_cases)
col2.metric("စစ်ဆေးဆဲ", investigating_count)
col3.metric("တရားစွဲတင်", court_count)
col4.metric("တရားခံပြေး", absconder_count)
col5.metric("ပြီးပြတ်", closed_count)
col6.metric("🗑️ အမှိုက်ပုံး", trash_count)

st.markdown("---")

# Navigation Tabs
tab1, tab2, tab3, tab4 = st.tabs(["📋 အမှုတွဲစာရင်း", "📊 အချက်အလက် ခွဲခြမ်းစိတ်ဖြာမှု (Analytics)", "➕ အမှုအသစ်ထည့်ရန်", "⚙️ အထူးကိရိယာများ (Backup/Excel Paste)"])

with tab1:
    st.subheader("အမှုတွဲများ ရှာဖွေစစ်ဆေးခြင်း")
    
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        sel_status = st.selectbox("အခြေအနေအလိုက် Filter", ["အားလုံး", "စစ်ဆေးဆဲ", "တရားစွဲတင်", "တရားခံပြေး", "ပြီးပြတ်/ပိတ်", "အမှိုက်ပုံး"], key="filter_status")
    with f_col2:
        reg_list = ["အားလုံး"] + list(active_df["region"].dropna().unique()) if not active_df.empty else ["အားလုံး"]
        sel_reg = st.selectbox("တိုင်းဒေသကြီး/ပြည်နယ်", reg_list, key="filter_reg")
    with f_col3:
        town_list = ["အားလုံး"] + list(active_df["township"].dropna().unique()) if not active_df.empty else ["အားလုံး"]
        sel_town = st.selectbox("မြို့နယ်", town_list, key="filter_town")
    with f_col4:
        search_query = st.text_input("🔍 ကီးဝပ်ဖြင့် ရှာဖွေရန်", key="filter_search")

    display_df = df.copy()
    if sel_status == "အမှိုက်ပုံး":
        display_df = display_df[display_df["isTrashed"] == 1]
    else:
        display_df = display_df[display_df["isTrashed"] == 0]
        if sel_status != "အားလုံး":
            display_df = display_df[display_df["status"] == sel_status]
            
    if sel_reg != "အားလုံး":
        display_df = display_df[display_df["region"] == sel_reg]
    if sel_town != "အားလုံး":
        display_df = display_df[display_df["township"] == sel_town]
        
    if search_query:
        mask = display_df.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        display_df = display_df[mask]

    st.write(f"တွေ့ရှိသော မှတ်တမ်းအရေအတွက်: **{len(display_df)}** ခု")

    for idx, row in display_df.iterrows():
        st.markdown(f"""
        <div style="background: white; padding: 12px; border-radius: 8px; border-left: 5px solid #2b6cb0; margin-bottom: 10px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <b>{row['region'] or ''} ၊ {row['township'] or ''}မြို့နယ် ({row['station'] or ''}) - {row['caseNo']}</b> 
            <span style="background: #ebf8ff; color: #2b6cb0; padding: 2px 6px; border-radius: 4px; font-size: 11px;">{row['status']}</span>
            <br><small><b>ပြစ်မှု/ပုဒ်မ:</b> {row['crime']} / {row['section']} | <b>တရားလို:</b> {row['complainantName']} | <b>တရားခံ:</b> {row['accusedName']} ({row['accusedStatus']})</small>
            <br><small><b>အမှုဖွင့်ရက်:</b> {row['date']} | <b>စစ်ဆေးသူ:</b> {row['officer']} | <b>တရားရုံးအမှုအမှတ်:</b> {row['courtCaseInfo'] or '-'}</small>
        </div>
        """, unsafe_allow_html=True)
        
        b_col1, b_col2, b_col3 = st.columns([1, 1, 6])
        with b_col1:
            if row["isTrashed"] == 1:
                if st.button("ပြန်ဖော်ရန်", key=f"restore_{row['id']}"):
                    run_query("UPDATE cases SET isTrashed = 0 WHERE id = ?", (row['id'],), fetch=False)
                    st.rerun()
            else:
                if st.button("အမှိုက်ပုံးသို့", key=f"trash_{row['id']}"):
                    run_query("UPDATE cases SET isTrashed = 1 WHERE id = ?", (row['id'],), fetch=False)
                    st.rerun()
        with b_col2:
            if row["isTrashed"] == 1:
                if st.button("အပြီးဖျက်", key=f"del_{row['id']}"):
                    if st.session_state.admin_auth:
                        run_query("DELETE FROM cases WHERE id = ?", (row['id'],), fetch=False)
                        st.rerun()
                    else:
                        st.error("Admin Login လိုအပ်ပါသည်။")

with tab2:
    st.subheader("အမှုတွဲအခြေအနေ ခွဲခြမ်းစိတ်ဖြာချက်များ")
    if not active_df.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### အမှုအခြေအနေ နှုန်းထား")
            status_counts = active_df["status"].value_counts()
            fig, ax = plt.subplots()
            ax.pie(status_counts, labels=status_counts.index, autopct='%1.1f%%', startangle=90, colors=['#dd6b20', '#3182ce', '#d53f8c', '#e53e3e'])
            ax.axis('equal')
            st.pyplot(fig)
        with c2:
            st.markdown("##### အဖြစ်များဆုံး ပြစ်မှုများ")
            crime_counts = active_df["crime"].value_counts().head(5)
            fig2, ax2 = plt.subplots()
            crime_counts.plot(kind='bar', ax=ax2, color='#2b6cb0')
            plt.xticks(rotation=45, ha='right')
            st.pyplot(fig2)
    else:
        st.info("ပြသရန် ဒေတာ မရှိသေးပါ။")

with tab3:
    st.subheader("အမှုတွဲအသစ် ထည့်သွင်းရန် ပုံစံ")
    with st.form("case_form"):
        r_col1, r_col2, r_col3 = st.columns(3)
        with r_col1:
            region = st.text_input("တိုင်းဒေသကြီး/ပြည်နယ်", value="နေပြည်တော်")
            station = st.text_input("ရဲစခန်းအမည်")
            crime = st.text_input("ပြစ်မှုအမျိုးအစား")
            date = st.date_input("အမှုဖွင့်ရက်စွဲ")
        with r_col2:
            district = st.text_input("ခရိုင်")
            caseNo = st.text_input("ပ အမှတ် (ဥပမာ - ပ ၁၂/၂၀၂၆)")
            section = st.text_input("ပုဒ်မ")
            officer = st.text_input("စစ်ဆေးမည့်အရာရှိ (IO)")
        with r_col3:
            township = st.text_input("မြို့နယ်")
            complainantName = st.text_input("တရားလို အမည်")
            accusedName = st.text_input("တရားခံ အမည်")
            accusedStatus = st.selectbox("တရားခံ အခြေအနေ", ["ဖမ်းမိ", "လွတ်မြောက်", "ဝရမ်းထုတ်", "ခံဝန်ဖြင့်လွှတ်"])

        o_col1, o_col2 = st.columns(2)
        with o_col1:
            courtCaseInfo = st.text_input("စွဲတင်သည့်တရားရုံးနှင့်အမှုအမှတ်")
            status = st.selectbox("အမှုတွဲအခြေအနေ", ["စစ်ဆေးဆဲ", "တရားစွဲတင်", "တရားခံပြေး", "ပြီးပြတ်/ပိတ်"])
        with o_col2:
            nrc = st.text_input("မှတ်ပုံတင်အမှတ် (NRC)")
            phone = st.text_input("ဖုန်းနံပါတ်")

        details = st.text_area("အမှုဖြစ်စဉ်အကျဉ်း / မှတ်ချက်")
        submitted = st.form_submit_button("မှတ်တမ်း သိမ်းဆည်းမည်")

        if submitted:
            run_query("""
                INSERT INTO cases (region, district, township, station, caseNo, crime, section, date, officer, complainantName, accusedName, accusedStatus, courtCaseInfo, nrc, phone, status, details)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (region, district, township, station, caseNo, crime, section, str(date), officer, complainantName, accusedName, accusedStatus, courtCaseInfo, nrc, phone, status, details), fetch=False)
            st.success("အမှုတွဲ အောင်မြင်စွာ သိမ်းဆည်းပြီးပါပြီ။")
            st.rerun()

with tab4:
    st.subheader("အထူးကိရိယာများနှင့် Backup / Excel Export")
    
    if not active_df.empty:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            active_df.to_excel(writer, index=False, sheet_name='Cases')
        excel_data = output.getvalue()
        st.download_button(
            label="📊 Excel ဖိုင်ဖြင့် ဒေါင်းလုဒ်ဆွဲရန်",
            data=excel_data,
            file_name=f"Police_Records_{datetime.now().strftime('%Y-%m-%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    
    st.markdown("---")
    st.write("### Excel Copy/Paste မှတစ်ဆင့် အချက်အလက်များ ထည့်သွင်းရန်")
    pasted_text = st.text_area("Excel မှ Copy ကူးထားသော ဒေတာများကို ဤနေရာတွင် Paste လုပ်ပါ")
    if st.button("Paste လုပ်ထားသော ဒေတာများကို ထည့်မည်"):
        if pasted_text:
            lines = pasted_text.strip().split("\n")
            count = 0
            for line in lines:
                cols = line.split("\t") if "\t" in line else line.split(",")
                if len(cols) >= 6:
                    run_query("""
                        INSERT INTO cases (region, district, township, station, caseNo, crime, section, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'စစ်ဆေးဆဲ')
                    """, (cols[0].strip(), cols[1].strip() if len(cols)>1 else "", cols[2].strip() if len(cols)>2 else "", 
                          cols[3].strip() if len(cols)>3 else "", cols[4].strip() if len(cols)>4 else "", 
                          cols[5].strip() if len(cols)>5 else "", cols[6].strip() if len(cols)>6 else ""), fetch=False)
                    count += 1
            st.success(f"အောင်မြင်စွာ ထည့်သွင်းနိုင်ခဲ့သော မှတ်တမ်းအရေအတွက်: {count} ခု")
            st.rerun()
sudo apt update
sudo apt install python3-pip python3-venv -y
streamlit run app.py --server.port=8501 --server.address=0.0.0.0


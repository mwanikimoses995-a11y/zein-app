import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from datetime import datetime

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School AI - Global", layout="wide")

FILES = {
    "schools": "schools.csv",
    "users": "users.csv",
    "students": "students.csv",
    "marks": "marks.csv",
    "attendance": "attendance.csv"
}

COLS = {
    "schools": ["school_name", "type", "status"],
    "users": ["username", "password", "role", "school", "phone"],
    "students": ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year"],
    "marks": ["adm_no", "school", "year", "term", "subject", "marks"],
    "attendance": ["adm_no", "school", "year", "term", "days_present"]
}

CURRENT_YEAR = str(datetime.now().year)
TERMS = ["Term 1", "Term 2", "Term 3"]
LEVEL_OPTIONS = {
    "Junior": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior": ["Grade 10", "Grade 11", "Grade 12"],
    "Both": ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
}

# =========================
# UTILITIES
# =========================
def hash_password(p):
    return hashlib.sha256(str(p).encode()).hexdigest()

def load_data(key):
    file = FILES[key]
    expected = COLS[key]
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=expected)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    for col in expected:
        if col not in df.columns: df[col] = ""
    return df

def save(df, key):
    df.to_csv(FILES[key], index=False)

# =========================
# INITIALIZATION
# =========================
schools = load_data("schools")
users = load_data("users")
students = load_data("students")
marks = load_data("marks")

# Data cleaning to ensure matching works perfectly
for df in [students, marks, users]:
    for col in ['adm_no', 'school', 'year', 'username', 'parent_phone']:
        if col in df.columns: 
            df[col] = df[col].astype(str).str.strip()

if "zein" not in users['username'].values:
    superadmin = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000"]], columns=COLS["users"])
    users = pd.concat([users, superadmin], ignore_index=True)
    save(users, "users")

# =========================
# LOGIN SYSTEM
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    with st.container(border=True):
        u = st.text_input("Username").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("Sign In", use_container_width=True):
            match = users[(users.username == u) & (users.password == hash_password(p))]
            if not match.empty:
                st.session_state.user = match.iloc[0].to_dict()
                st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

logged_in_user = st.session_state.user
role = logged_in_user["role"]
my_school = str(logged_in_user["school"])

st.sidebar.title("Zein AI")
st.sidebar.info(f"User: {logged_in_user['username']}\nSchool: {my_school}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ROLE LOGIC
# =========================

if role == "superadmin":
    st.header("🌐 Global Master Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        s_name = st.text_input("Institution Name")
        s_type = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if s_name and s_name not in schools['school_name'].values:
                schools = pd.concat([schools, pd.DataFrame([[s_name, s_type, "Active"]], columns=COLS["schools"])], ignore_index=True)
                save(schools, "schools")
                new_a = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000"]], columns=COLS["users"])
                users = pd.concat([users, new_a], ignore_index=True)
                save(users, "users")
                st.success("School Activated!"); st.rerun()
    with c2: st.dataframe(schools, use_container_width=True)

elif role == "admin":
    if my_school not in schools['school_name'].values:
        schools = pd.concat([schools, pd.DataFrame([[my_school, "Both", "Active"]], columns=COLS["schools"])], ignore_index=True)
        save(schools, "schools"); st.rerun()

    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    st.header(f"🏫 Admin Dashboard: {my_school}")
    t1, t2 = st.tabs(["Enrollment", "Staff Management"])
    
    with t1:
        with st.form("enroll"):
            adm, name = st.text_input("ADM Number").strip(), st.text_input("Full Name").strip()
            phone = st.text_input("Parent Phone (Login Username)").strip()
            grade = st.selectbox("Grade", LEVEL_OPTIONS.get(sch_type, ["Grade 7"]))
            if st.form_submit_button("Enroll Student"):
                if adm and name and phone:
                    students = pd.concat([students, pd.DataFrame([[adm, "", name, grade, my_school, phone, CURRENT_YEAR]], columns=COLS["students"])], ignore_index=True)
                    save(students, "students")
                    u_s = [adm, hash_password("1234"), "student", my_school, phone]
                    u_p = [phone, hash_password(phone), "parent", my_school, phone]
                    users = pd.concat([users, pd.DataFrame([u_s, u_p], columns=COLS["users"])], ignore_index=True).drop_duplicates('username', keep='last')
                    save(users, "users"); st.success("Enrollment Data Saved.")

    with t2:
        tu, tp = st.text_input("Teacher Username"), st.text_input("Password", type="password")
        if st.button("Create Teacher Account"):
            users = pd.concat([users, pd.DataFrame([[tu, hash_password(tp), "teacher", my_school, "000"]], columns=COLS["users"])], ignore_index=True).drop_duplicates('username', keep='last')
            save(users, "users"); st.success("Account Created.")

elif role == "teacher":
    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    st.header("📝 Marks Entry")
    sel_cls = st.sidebar.selectbox("Select Grade", LEVEL_OPTIONS.get(sch_type, []))
    sel_term = st.sidebar.selectbox("Select Term", TERMS)
    cls_stds = students[(students.school == my_school) & (students['class'] == sel_cls)]
    
    if not cls_stds.empty:
        subj = st.text_input("Subject (e.g. English, Science)").strip()
        if subj:
            df_entry = pd.DataFrame({"adm_no": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Marks": 0.0})
            edited = st.data_editor(df_entry, use_container_width=True, hide_index=True)
            if st.button("Submit Grades"):
                new_rows = [[str(r['adm_no']), my_school, CURRENT_YEAR, sel_term, subj, r['Marks']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_rows, columns=COLS["marks"])], ignore_index=True)
                marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                save(marks, "marks"); st.success("Grades Submitted Successfully.")
    else: st.info("No students enrolled in this grade.")

elif role in ["parent", "student"]:
    st.header("📊 Performance Hub")
    
    # Identify which students to display
    search_val = logged_in_user['username']
    if role == 'parent':
        my_records = students[students['parent_phone'] == search_val]
    else:
        my_records = students[students['adm_no'] == search_val]
    
    if not my_records.empty:
        selected_adm = st.selectbox("Switch Profile", my_records.adm_no.unique())
        std_info = my_records[my_records.adm_no == selected_adm].iloc[0]
        st.subheader(f"Results for {std_info['name']} ({std_info['class']})")
        
        std_marks = marks[(marks.adm_no == selected_adm) & (marks.year == CURRENT_YEAR)]
        
        if not std_marks.empty:
            # Table View
            report = std_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-")
            st.dataframe(report, use_container_width=True)
            
            # --- BAR CHART ANALYSIS ---
            st.divider()
            st.subheader("📈 Subject Performance Analysis")
            
            # Prepare data for Bar Chart: Subjects on X-axis, Marks on Y-axis, Color by Term
            chart_data = std_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last')
            # Ensure terms are ordered
            chart_data = chart_data.reindex(columns=[t for t in TERMS if t in chart_data.columns])
            
            
            st.bar_chart(chart_data)
            
            st.caption("The bar chart compares your performance across all terms for each subject recorded.")
        else: st.warning("No grades have been uploaded for the current year.")
    else: st.error("No student records linked to this account.")

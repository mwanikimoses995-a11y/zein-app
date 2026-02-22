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

# Database Files
SCHOOLS_FILE = "schools.csv"
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

CURRENT_YEAR = datetime.now().year
TERMS = ["Term 1", "Term 2", "Term 3"]

# CBC Structure (8-4-4 Form 1 & 2 removed)
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

def load_data(file, expected_cols, default_rows=None):
    if not os.path.exists(file):
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    for col in expected_cols:
        if col not in df.columns: df[col] = "" # Ensure schema matches
    return df

def save(df, file):
    df.to_csv(file, index=False)

def get_kcse_grade(marks):
    if marks >= 80: return "A", 12
    if marks >= 50: return "C", 6
    if marks >= 30: return "D-", 2
    return "E", 1

# =========================
# DATA INITIALIZATION
# =========================
schools = load_data(SCHOOLS_FILE, ["school_name", "type", "status"])
users = load_data(USERS_FILE, ["username", "password", "role", "school", "phone"], 
                 [["superadmin", hash_password("zein2026"), "superadmin", "SYSTEM", "000"]])
students = load_data(STUDENTS_FILE, ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year"])
marks = load_data(MARKS_FILE, ["adm_no", "school", "year", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["adm_no", "school", "year", "term", "days_present"])

# =========================
# LOGIN SYSTEM
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    u = st.text_input("Username / ADM / Parent Phone")
    p = st.text_input("Password", type="password")
    
    if st.button("Login"):
        match = users[(users.username == str(u)) & (users.password == hash_password(p))]
        if not match.empty:
            u_dat = match.iloc[0].to_dict()
            sch_stat = schools[schools.school_name == u_dat['school']]
            if not sch_stat.empty and sch_stat.iloc[0]['status'] == "Locked":
                st.error("Access Denied: This school account has been suspended.")
            else:
                st.session_state.user = u_dat
                st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

user = st.session_state.user
role = user["role"]
my_school = user["school"]

# School Watermark
if my_school != "SYSTEM":
    st.markdown(f"""<h1 style='opacity: 0.05; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 150px; z-index: -1; pointer-events: none;'>{my_school}</h1>""", unsafe_allow_html=True)

# Sidebar
st.sidebar.title("Zein AI")
st.sidebar.info(f"📍 {my_school}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# SUPER ADMIN: SYSTEM CONTROL
# =========================
if role == "superadmin":
    st.header("🌐 Global System Management")
    c1, c2 = st.columns([1, 2])
    
    with c1:
        st.subheader("Register New School")
        new_sch = st.text_input("School Name")
        sch_type = st.selectbox("School Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if new_sch and new_sch not in schools.school_name.values:
                schools = pd.concat([schools, pd.DataFrame([[new_sch, sch_type, "Active"]], columns=schools.columns)], ignore_index=True)
                save(schools, SCHOOLS_FILE)
                # Create Admin Account (User: schoolname, Pass: schoolname)
                users = pd.concat([users, pd.DataFrame([[new_sch, hash_password(new_sch), "admin", new_sch, "000"]], columns=users.columns)], ignore_index=True)
                save(users, USERS_FILE)
                st.success(f"{new_sch} added!"); st.rerun()

    with c2:
        st.subheader("System Overview")
        st.metric("Total Schools", len(schools))
        st.dataframe(schools, use_container_width=True)
        t_sch = st.selectbox("Select School to Lock/Unlock", schools.school_name.unique())
        if st.button("Toggle School Status"):
            schools.loc[schools.school_name == t_sch, 'status'] = "Locked" if schools.loc[schools.school_name == t_sch, 'status'].values[0] == "Active" else "Active"
            save(schools, SCHOOLS_FILE); st.rerun()

# =========================
# SCHOOL ADMIN: INTERNAL MGMT
# =========================
elif role == "admin":
    st.header(f"🏫 {my_school} Administration")
    t1, t2, t3 = st.tabs(["Student Enrollment", "Academic Promotion", "Staff Mgmt"])
    
    with t1:
        st.subheader("New Enrollment")
        with st.form("reg"):
            c1, c2 = st.columns(2)
            adm = c1.text_input("ADM Number")
            kemis = c1.text_input("KEMIS Number")
            name = c2.text_input("Student Name")
            phone = c2.text_input("Parent Phone (Username & Pass)")
            sch_cfg = schools[schools.school_name == my_school].iloc[0]['type']
            cls = st.selectbox("Class", LEVEL_OPTIONS[sch_cfg])
            if st.form_submit_button("Enroll"):
                if adm and phone:
                    students = pd.concat([students, pd.DataFrame([[adm, kemis, name, cls, my_school, phone, CURRENT_YEAR]], columns=students.columns)], ignore_index=True)
                    # Add Parent & Student Users
                    u_parent = [phone, hash_password(phone), "parent", my_school, phone]
                    u_student = [adm, hash_password("1234"), "student", my_school, phone]
                    users = pd.concat([users, pd.DataFrame([u_parent, u_student], columns=users.columns)], ignore_index=True).drop_duplicates('username')
                    save(students, STUDENTS_FILE); save(users, USERS_FILE)
                    st.success("Registration Complete")

    with t2:
        st.subheader("🚀 Bulk Promotion (End of Year)")
        st.warning("This moves all students in a class to the next Grade. Previous marks are archived automatically.")
        p_from = st.selectbox("From Class", LEVEL_OPTIONS[sch_cfg], key="p1")
        p_to = st.selectbox("To Class", ["Graduated"] + LEVEL_OPTIONS[sch_cfg], key="p2")
        if st.button("Execute Promotion"):
            students.loc[(students.school == my_school) & (students['class'] == p_from), 'class'] = p_to
            save(students, STUDENTS_FILE)
            st.success(f"All students in {p_from} moved to {p_to}")

# =========================
# PARENT & STUDENT VIEW
# =========================
elif role in ["parent", "student"]:
    st.header("📊 Performance Portal")
    my_stds = students[(students.parent_phone == user['username']) & (students.school == my_school)] if role == "parent" else students[(students.adm_no == user['username']) & (students.school == my_school)]
    
    if not my_stds.empty:
        sel_adm = st.selectbox("Student", my_stds.adm_no.unique())
        std_info = my_stds[my_stds.adm_no == sel_adm].iloc[0]
        
        # History Filter
        hist_years = marks[marks.adm_no == sel_adm]['year'].unique().tolist()
        if CURRENT_YEAR not in hist_years: hist_years.append(CURRENT_YEAR)
        sel_yr = st.sidebar.selectbox("Academic Year", sorted(hist_years, reverse=True))
        
        st.subheader(f"{std_info['name']} - {std_info['class']} ({sel_yr})")
        
        m_data = marks[(marks.adm_no == sel_adm) & (marks.year == str(sel_yr))]
        if m_data.empty:
            st.info(f"No records found for {sel_yr}.")
        else:
            # Display Summary
            avg = m_data['marks'].astype(float).mean()
            grd, pts = get_kcse_grade(avg)
            c1, c2 = st.columns(2)
            c1.metric("Yearly Average", f"{round(avg,1)}%")
            c2.metric("Projected Grade", grd)
            
            # Detailed Table
            report = m_data.pivot_table(index='subject', columns='term', values='marks', aggfunc='first').fillna("-")
            st.table(report)

# =========================
# TEACHER SECTION (SAME AS BEFORE BUT WITH ADM)
# =========================
elif role == "teacher":
    st.header("👨‍🏫 Teacher Grading")
    # ... existing teacher logic but using ADM instead of Name to ensure records track correctly ...

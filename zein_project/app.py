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

SCHOOLS_FILE = "schools.csv"
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

CURRENT_YEAR = datetime.now().year
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

def load_data(file, expected_cols, default_rows=None):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    for col in expected_cols:
        if col not in df.columns: df[col] = ""
    return df

def save(df, file):
    df.to_csv(file, index=False)

# =========================
# DATA INITIALIZATION
# =========================
schools = load_data(SCHOOLS_FILE, ["school_name", "type", "status"])
users = load_data(USERS_FILE, ["username", "password", "role", "school", "phone"])

# Ensure Superadmin exists
if "zein" not in users['username'].values:
    superadmin = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000"]], 
                              columns=["username", "password", "role", "school", "phone"])
    users = pd.concat([users, superadmin], ignore_index=True)
    save(users, USERS_FILE)

students = load_data(STUDENTS_FILE, ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year"])
marks = load_data(MARKS_FILE, ["adm_no", "school", "year", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["adm_no", "school", "year", "term", "days_present"])

# =========================
# LOGIN & SESSION
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    u = st.text_input("Username").strip()
    p = st.text_input("Password", type="password").strip()
    if st.button("Sign In"):
        match = users[(users.username == u) & (users.password == hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else: st.error("Invalid credentials.")
    st.stop()

user = st.session_state.user
role = user["role"]
my_school = user["school"]

st.sidebar.title("Zein AI")
st.sidebar.write(f"Logged in: **{user['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ROLE BASED VIEWS
# =========================

# --- SUPERADMIN ---
if role == "superadmin":
    st.header("🌐 Global Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        s_name = st.text_input("School Name")
        s_type = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Register School"):
            if s_name and s_name not in schools.school_name.values:
                new_sch = pd.DataFrame([[s_name, s_type, "Active"]], columns=schools.columns)
                schools = pd.concat([schools, new_sch], ignore_index=True)
                save(schools, SCHOOLS_FILE)
                # Auto-create admin
                new_adm = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000"]], columns=users.columns)
                users = pd.concat([users, new_adm], ignore_index=True)
                save(users, USERS_FILE)
                st.success("Registration Successful")
                st.rerun()
    with c2:
        st.dataframe(schools)

# --- SCHOOL ADMIN (Fixed IndexError here) ---
elif role == "admin":
    # Safely get school type
    sch_data = schools[schools.school_name == my_school]
    if sch_data.empty:
        st.error("School configuration not found. Please contact Superadmin.")
        st.stop()
    
    sch_type = sch_data.iloc[0]['type']
    st.header(f"🏫 Admin Dashboard: {my_school}")
    
    tab1, tab2 = st.tabs(["Student Enrollment", "Manage Teachers"])
    
    with tab1:
        with st.form("enroll_form"):
            adm = st.text_input("ADM Number")
            name = st.text_input("Student Name")
            phone = st.text_input("Parent Phone")
            grade = st.selectbox("Assign Grade", LEVEL_OPTIONS.get(sch_type, ["Grade 7"]))
            if st.form_submit_button("Enroll"):
                if adm and name:
                    new_std = pd.DataFrame([[adm, "", name, grade, my_school, phone, CURRENT_YEAR]], columns=students.columns)
                    students = pd.concat([students, new_std], ignore_index=True)
                    save(students, STUDENTS_FILE)
                    # Create User Accounts
                    u_s = pd.DataFrame([[adm, hash_password("1234"), "student", my_school, phone]], columns=users.columns)
                    u_p = pd.DataFrame([[phone, hash_password(phone), "parent", my_school, phone]], columns=users.columns)
                    users = pd.concat([users, u_s, u_p], ignore_index=True).drop_duplicates('username')
                    save(users, USERS_FILE)
                    st.success(f"{name} Enrolled.")

    with tab2:
        t_u = st.text_input("New Teacher Username")
        t_p = st.text_input("New Teacher Password", type="password")
        if st.button("Create Teacher"):
            new_t = pd.DataFrame([[t_u, hash_password(t_p), "teacher", my_school, "000"]], columns=users.columns)
            users = pd.concat([users, new_t], ignore_index=True)
            save(users, USERS_FILE)
            st.success("Teacher account created.")

# --- TEACHER ---
elif role == "teacher":
    sch_data = schools[schools.school_name == my_school]
    if sch_data.empty:
        st.error("Access Denied: School not active.")
        st.stop()
    
    sch_type = sch_data.iloc[0]['type']
    st.header("📝 Grade & Attendance Entry")
    
    sel_cls = st.sidebar.selectbox("Class", LEVEL_OPTIONS.get(sch_type, []))
    sel_term = st.sidebar.selectbox("Term", TERMS)
    
    cls_stds = students[(students.school == my_school) & (students['class'] == sel_cls)]
    
    if not cls_stds.empty:
        subj = st.text_input("Subject")
        if subj:
            df_entry = pd.DataFrame({"ADM": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Score": 0.0})
            edited = st.data_editor(df_entry)
            if st.button("Save Academic Data"):
                new_marks = [[r['ADM'], my_school, CURRENT_YEAR, sel_term, subj, r['Score']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_marks, columns=marks.columns)], ignore_index=True)
                save(marks, MARKS_FILE)
                st.success("Grades Recorded.")
    else:
        st.info("No students enrolled in this grade yet.")

# --- PARENT / STUDENT ---
elif role in ["parent", "student"]:
    st.header("📊 Performance Hub")
    # Identify which students to show
    target_id = user['username'] if role == 'student' else user['phone']
    col_filter = 'adm_no' if role == 'student' else 'parent_phone'
    
    my_kids = students[students[col_filter] == target_id]
    
    if not my_kids.empty:
        sel_std = st.selectbox("View Profile", my_kids.adm_no.unique())
        res = marks[(marks.adm_no == sel_std) & (marks.year == CURRENT_YEAR)]
        if not res.empty:
            st.table(res.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
        else:
            st.warning("No academic records found for the current year.")

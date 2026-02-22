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

def load_data(file, expected_cols):
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    return pd.read_csv(file)

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

user = st.session_state.user
role = user["role"]
my_school = user["school"]

st.sidebar.title("Zein AI")
st.sidebar.info(f"User: {user['username']}\n\nSchool: {my_school}")
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
        st.subheader("Register New School")
        s_name = st.text_input("Institution Name")
        s_type = st.selectbox("Education Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if s_name:
                # Add to schools
                new_s = pd.DataFrame([[s_name, s_type, "Active"]], columns=schools.columns)
                schools = pd.concat([schools, new_s], ignore_index=True)
                save(schools, SCHOOLS_FILE)
                # Create the Admin for that school
                new_a = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000"]], columns=users.columns)
                users = pd.concat([users, new_a], ignore_index=True)
                save(users, USERS_FILE)
                st.success("School Registered!")
                st.rerun()
    with c2:
        st.subheader("System Institutions")
        st.dataframe(schools, use_container_width=True)

elif role == "admin":
    # SELF-HEALING: If school entry is missing, create a default one
    if my_school not in schools['school_name'].values:
        default_entry = pd.DataFrame([[my_school, "Both", "Active"]], columns=schools.columns)
        schools = pd.concat([schools, default_entry], ignore_index=True)
        save(schools, SCHOOLS_FILE)
        st.rerun()

    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    st.header(f"🏫 Admin: {my_school}")
    
    t1, t2 = st.tabs(["Enrollment", "Staff Management"])
    
    with t1:
        with st.form("enroll"):
            st.write("### New Student Registration")
            col1, col2 = st.columns(2)
            adm = col1.text_input("ADM Number")
            name = col1.text_input("Student Full Name")
            phone = col2.text_input("Parent Phone Number")
            grade = col2.selectbox("Grade", LEVEL_OPTIONS[sch_type])
            if st.form_submit_button("Enroll Student"):
                if adm and name:
                    # Update Students CSV
                    new_std = pd.DataFrame([[adm, "", name, grade, my_school, phone, CURRENT_YEAR]], columns=students.columns)
                    students = pd.concat([students, new_std], ignore_index=True)
                    save(students, STUDENTS_FILE)
                    # Create User Accounts (Student pass: 1234 | Parent pass: phone)
                    u_s = [adm, hash_password("1234"), "student", my_school, phone]
                    u_p = [phone, hash_password(phone), "parent", my_school, phone]
                    new_usrs = pd.DataFrame([u_s, u_p], columns=users.columns)
                    users = pd.concat([users, new_usrs], ignore_index=True).drop_duplicates('username')
                    save(users, USERS_FILE)
                    st.success(f"Enrolled {name} successfully!")

    with t2:
        st.write("### Register Teacher")
        tu = st.text_input("Teacher Username")
        tp = st.text_input("Teacher Password", type="password")
        if st.button("Create Account"):
            if tu and tp:
                new_t = pd.DataFrame([[tu, hash_password(tp), "teacher", my_school, "000"]], columns=users.columns)
                users = pd.concat([users, new_t], ignore_index=True)
                save(users, USERS_FILE)
                st.success("Teacher account active.")

elif role == "teacher":
    # Ensure teacher belongs to a valid school
    if my_school not in schools['school_name'].values:
        st.error("School configuration missing. Please ask your Admin to re-save school settings.")
        st.stop()

    st.header("📝 Grading Portal")
    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    sel_cls = st.sidebar.selectbox("Class", LEVEL_OPTIONS[sch_type])
    sel_term = st.sidebar.selectbox("Term", TERMS)
    
    cls_stds = students[(students.school == my_school) & (students['class'] == sel_cls)]
    
    if cls_stds.empty:
        st.warning(f"No students found in {sel_cls}")
    else:
        subj = st.text_input("Enter Subject (e.g., Mathematics)")
        if subj:
            df_entry = pd.DataFrame({"ADM": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Marks": 0.0})
            edited = st.data_editor(df_entry, use_container_width=True)
            if st.button("Save All Grades"):
                new_m = [[r['ADM'], my_school, CURRENT_YEAR, sel_term, subj, r['Marks']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_m, columns=marks.columns)], ignore_index=True)
                save(marks, MARKS_FILE)
                st.success(f"Marks for {subj} saved!")

elif role in ["parent", "student"]:
    st.header("📊 Performance Results")
    search_key = user['username'] if role == 'student' else user['phone']
    col_name = 'adm_no' if role == 'student' else 'parent_phone'
    
    my_records = students[students[col_name] == search_key]
    
    if not my_records.empty:
        selected_adm = st.selectbox("Student Profile", my_records.adm_no.unique())
        res = marks[(marks.adm_no == selected_adm) & (marks.year == CURRENT_YEAR)]
        if not res.empty:
            st.table(res.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
        else:
            st.info("No exam results found for this year yet.")

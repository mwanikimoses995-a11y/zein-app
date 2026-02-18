import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Advanced School ERP AI", layout="wide")

# ==========================
# FILES
# ==========================
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
RESULTS_FILE = "results.csv"
ATTENDANCE_FILE = "attendance.csv"

TERMS = ["Term 1", "Term 2", "Term 3"]
TERM_ORDER = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4"]

# ==========================
# SUBJECTS
# ==========================
COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
GROUP_1 = ["Physics", "CRE", "IRE", "HRE"]
GROUP_2 = ["History", "Geography"]
GROUP_3 = ["Business", "Agriculture", "Computer", "French", "German", "Arabic"]
GROUP_4 = ["Wood Technology", "Metal Work", "Building Construction", "Electricity"]

ALL_SUBJECTS = COMPULSORY + GROUP_1 + GROUP_2 + GROUP_3 + GROUP_4

# ==========================
# UTILS
# ==========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_file(file, columns, default=None):
    if not os.path.exists(file):
        pd.DataFrame(default if default else [], columns=columns).to_csv(file, index=False)

def save(df, file):
    df.to_csv(file, index=False)

def safe_columns(df, cols):
    for c in cols:
        if c not in df.columns:
            df[c] = None
    return df

def load():
    users = pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame()
    students = pd.read_csv(STUDENTS_FILE) if os.path.exists(STUDENTS_FILE) else pd.DataFrame()
    marks = pd.read_csv(MARKS_FILE) if os.path.exists(MARKS_FILE) else pd.DataFrame()
    results = pd.read_csv(RESULTS_FILE) if os.path.exists(RESULTS_FILE) else pd.DataFrame()
    attendance = pd.read_csv(ATTENDANCE_FILE) if os.path.exists(ATTENDANCE_FILE) else pd.DataFrame()

    users = safe_columns(users, ["username","password","role","subject"])
    students = safe_columns(students, ["student_name","class_level"])
    marks = safe_columns(marks, ["student","class_level","term","subject","marks"])
    results = safe_columns(results, ["student","class_level","term","total","average","grade","rank"])
    attendance = safe_columns(attendance, ["student","class_level","term","days_present","total_days","attendance_percent"])

    return users, students, marks, results, attendance

def grade(avg):
    if avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "E"

# ==========================
# CREATE FILES IF NOT EXIST
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"], [["admin", hash_password("1234"), "admin", ""]])
create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

# ==========================
# LOGIN
# ==========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        users, students, marks, results, attendance = load()
        match = users[(users["username"]==u) & (users["password"]==hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

users, students, marks, results, attendance = load()
user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 {user['username']} ({role})")
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# ==========================
# ADMIN DASHBOARD
# ==========================
if role=="admin":
    st.header("🛠 Admin Dashboard")
    tab1, tab2, tab3, tab4 = st.tabs(["Add Student","Add Teacher","View Users","Manage Users"])

    with tab1:
        st.subheader("➕ Add Student")
        name = st.text_input("Student Name")
        cls = st.selectbox("Class Level", CLASSES)
        if st.button("Add Student"):
            if not name: st.error("Enter name")
            elif name in students["student_name"].values: st.error("Student exists")
            else:
                new_student = pd.DataFrame([{"student_name": name, "class_level": cls}])
                students = pd.concat([students, new_student], ignore_index=True)
                save(students, STUDENTS_FILE)
                new_user = pd.DataFrame([{"username": name, "password": hash_password("1234"), "role":"student","subject":""}])
                users = pd.concat([users,new_user],ignore_index=True)
                save(users,USERS_FILE)
                st.success(f"Student {name} added with password 1234")
                st.experimental_rerun()

    with tab2:
        st.subheader("➕ Add Teacher")
        subject = st.selectbox("Subject", ALL_SUBJECTS)
        number = st.number_input("Teacher Number",1,20,1)
        username = f"{subject.lower()}{number}"
        st.info(f"Username: {username}")
        if st.button("Add Teacher"):
            if username in users["username"].values: st.error("Teacher exists")
            else:
                new_user = pd.DataFrame([{"username": username,"password":hash_password("1234"),"role":"teacher","subject":subject}])
                users = pd.concat([users,new_user],ignore_index=True)
                save(users,USERS_FILE)
                st.success(f"Teacher {username} added with password 1234")
                st.experimental_rerun()

    with tab3:
        st.subheader("👥 All Users")
        if not users.empty:
            display = users[["username","role","subject"]].copy()
            display["Password"] = "1234"
            st.dataframe(display,use_container_width=True)
            st.subheader("📊 User Stats")
            col1,col2,col3 = st.columns(3)
            col1.metric("Total Users", len(users))
            col2.metric("Teachers", len(users[users["role"]=="teacher"]))
            col3.metric("Students", len(users[users["role"]=="student"]))

    with tab4:
        st.subheader("🗑 Remove User")
        remove_user = st.selectbox("Select User", users["username"].values)
        if st.button("Remove User"):
            users = users[users["username"]!=remove_user]
            save(users,USERS_FILE)
            st.success(f"User {remove_user} removed")
            st.experimental_rerun()

# ==========================
# TEACHER DASHBOARD
# ==========================
elif role=="teacher":
    st.header("👩‍🏫 Teacher Dashboard")
    selected_class = st.selectbox("Select Class", CLASSES)
    selected_term = st.selectbox("Select Term", TERMS)
    class_students = students[students["class_level"]==selected_class]
    if class_students.empty: st.warning("No students"); st.stop()
    selected_student = st.se_

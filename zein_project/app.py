import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School ERP AI", layout="wide")

USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

MAX_SCHOOL_DAYS = 65 

TERMS = ["Term 1", "Term 2", "Term 3"]
TERM_ORDER = {term: i for i, term in enumerate(TERMS)}
TERM_INDEX = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4"]

COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
HUMANITIES = ["History", "Geography"]
SCIENCE_REL = ["CRE", "Physics"]
TECHNICAL = ["Business", "Computer", "Agriculture"]

# =========================
# UTILITIES
# =========================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_data(file, expected_cols, default_rows=None):
    if not os.path.exists(file):
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    if list(df.columns) != expected_cols:
        df = df.reindex(columns=expected_cols).fillna(0)
        df.to_csv(file, index=False)
    return df

def save(df, file):
    df.to_csv(file, index=False)

def get_kcse_grade(marks):
    if marks >= 80: return "A", 12
    if marks >= 75: return "A-", 11
    if marks >= 70: return "B+", 10
    if marks >= 65: return "B", 9
    if marks >= 60: return "B-", 8
    if marks >= 55: return "C+", 7
    if marks >= 50: return "C", 6
    if marks >= 45: return "C-", 5
    if marks >= 40: return "D+", 4
    if marks >= 35: return "D", 3
    if marks >= 30: return "D-", 2
    return "E", 1

def zein_predict(scores, terms):
    if len(scores) < 2: return scores[-1] if scores else 0
    try:
        coef = np.polyfit(terms, scores, 1)
        next_term = max(terms) + 1
        prediction = coef[0] * next_term + coef[1]
        return max(0, min(100, prediction))
    except: 
        return scores[-1]

# =========================
# INITIALIZE DATA
# =========================
users = load_data(USERS_FILE, ["username", "password", "role"], [["admin", hash_password("1234"), "admin"]])
students = load_data(STUDENTS_FILE, ["student", "class"])
marks = load_data(MARKS_FILE, ["student", "class", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["student", "class", "term", "days_present"])

# =========================
# LOGIN
# =========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        match = users[(users.username == u) & (users.password == hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else: st.error("Invalid credentials")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.title("Zein ERP")
st.sidebar.write(f"👤 **{user['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN / TEACHER SECTIONS
# =========================
if role == "admin":
    st.header("🛠 Admin Dashboard")
    t1, t2 = st.tabs(["Add Accounts", "System Clean-up"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Add Student")
            s_name = st.text_input("Full Name")
            s_cls = st.selectbox("Assign Class", CLASSES)
            if st.button("Create Student"):
                if s_name and s_name not in users.username.values:
                    users.loc[len(users)] = [s_name, hash_password("1234"), "student"]
                    students.loc[len(students)] = [s_name, s_cls]
                    save(users, USERS_FILE); save(students, STUDENTS_FILE)
                    st.success(f"Added {s_name}"); st.rerun()
        with c2:
            st.subheader("Add Teacher")
            t_name = st.text_input("Teacher Username")
            if st.button("Create Teacher"):
                if t_name and t_name not in users.username.values:
                    users.loc[len(users)] = [t_name, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success(f"Added {t_name}"); st.rerun()
    with t2:
        target_list = users[users.username != "admin"]["username"].tolist()
        if target_list:
            target = st.selectbox("Select User to Remove", target_list)
            if st.button("🔥 Delete User"):
                users = users[users.username != target]
                save(users, USERS_FILE); st.rerun()

elif role == "teacher":
    st.header("👩‍🏫 Academic Management")
    col1, col2, col3 = st.columns(3)
    sel_cls = col1.selectbox("Select Class", CLASSES)
    sel_term = col2.selectbox("Select Term", TERMS)
    class_students = students[students["class"] == sel_cls]["student"].tolist()
    
    if not class_students:
        st.warning(f"No students found in {sel_cls}.")
    else:
        sel_student = col3.selectbox("Target Student", ["-- All Students --"] + class_students)
        tab_m, tab_a = st.tabs(["Subject Grading", "Attendance (Days)"])
        
        with tab_m:
            c_h, c_s, c_t = st.columns(3)
            h_sub = c_h.selectbox("Humanity", HUMANITIES)
            s_sub = c_s.selectbox("Science", SCIENCE_REL)
            t_sub = c_t.selectbox("Technical", TECHNICAL)
            all_subs = COMPULSORY + [h_sub, s_sub, t_sub]
            
            if sel_student == "-- All Students --":
                for subj in all_subs:
                    with st.expander(f"Bulk Edit: {subj}"):
                        m_list = [marks[(marks.student==s)&(marks.term==sel_term)&(marks.subject==subj)]["marks"].values[0] if not marks[(marks.student==s)&(marks.term==

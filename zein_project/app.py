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

COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
GROUP_HUMANITIES = ["History", "Geography"]
GROUP_TECH = ["CRE", "Physics"]

# ==========================
# UTILITIES
# ==========================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_file(file, columns, default=None):
    if not os.path.exists(file):
        pd.DataFrame(default if default else [], columns=columns).to_csv(file, index=False)

def save_data(df, file):
    df.to_csv(file, index=False)

def load_data():
    users = pd.read_csv(USERS_FILE)
    students = pd.read_csv(STUDENTS_FILE)
    marks = pd.read_csv(MARKS_FILE)
    results = pd.read_csv(RESULTS_FILE)
    attendance = pd.read_csv(ATTENDANCE_FILE)
    return users, students, marks, results, attendance

def grade(avg):
    if avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "E"

# ==========================
# INITIAL FILE CREATION
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"],
            [["admin", hash_password("1234"), "admin", ""]])

create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

users, students, marks, results, attendance = load_data()

# ==========================
# LOGIN
# ==========================
if "user" not in st.session_state:

    st.title("🎓 Zein School ERP Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        match = users[
            (users["username"] == username) &
            (users["password"] == hash_password(password))
        ]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid login")

    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 {user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# ==========================
# STUDENT DASHBOARD
# ==========================
if role == "student":

    st.header("📊 Student Dashboard")

    student_name = user["username"]

    users, students, marks, results, attendance = load_data()

    student_marks = marks[marks["student"] == student_name]
    student_attendance = attendance[attendance["student"] == student_name]

    if student_marks.empty:
        st.warning("No marks yet.")
        st.stop()

    # Latest Term
    latest_term = student_marks["term"].map(TERM_ORDER).idxmax()
    latest_term_name = student_marks.loc[latest_term]["term"]

    latest_marks = student_marks[student_marks["term"] == latest_term_name]

    mean_mark = latest_marks["marks"].mean()

    st.metric("Mean Mark", round(mean_mark,2))
    st.metric("Grade", grade(mean_mark))

    # AI Prediction
    st.subheader("🔮 AI Next Term Prediction")

    predicted = []

    for subject in student_marks["subject"].unique():
        subj = student_marks[student_marks["subject"] == subject].copy()
        subj["term_order"] = subj["term"].map(TERM_ORDER)
        subj = subj.sort_values("term_order")

        if len(subj) < 2:
            pred = subj["marks"].iloc[-1]
        else:
            X = np.arange(len(subj)).reshape(-1,1)
            y = subj["marks"].values
            model = LinearRegression()
            model.fit(X,y)
            pred = model.predict([[len(subj)]])[0]

        pred = max(0, min(100, pred))
        predicted.append(pred)

    expected_mean = np.mean(predicted)

    st.metric("Expected Mean Next Term", round(expected_mean,2))
    st.metric("Expected Grade", grade(expected_mean))

    # Attendance
    st.subheader("📋 Attendance")

    if not student_attendance.empty:
        st.dataframe(student_attendance)

# ==========================
# ADMIN DASHBOARD
# ==========================
elif role == "admin":

    st.header("🛠 Admin Dashboard")

    users, students, marks, results, attendance = load_data()

    # ADD USERS
    st.subheader("➕ Add User")

    user_type = st.selectbox("User Type", ["Student","Teacher"])

    if user_type == "Student":
        name = st.text_input("Student Name")
        cls = st.selectbox("Class", CLASSES)

        if st.button("Add Student"):
            if name not in users["username"].values:
                students.loc[len(students)] = [name, cls]
                users.loc[len(users)] = [name, hash_password("1234"), "student", ""]
                save_data(students, STUDENTS_FILE)
                save_data(users, USERS_FILE)
                st.success("Student Added")

    if user_type == "Teacher":
        subject = st.text_input("Subject")
        number = st.text_input("Number")

        if st.button("Add Teacher"):
            username = f"{subject}{number}"
            if username not in users["username"].values:
                users.loc[len(users)] = [username, hash_password("1234"), "teacher", subject]
                save_data(users, USERS_FILE)
                st.success("Teacher Added")

    # VIEW USERS
    st.subheader("👥 All Users")
    st.dataframe(users)

    # REMOVE USER
    remove_user = st.selectbox("Remove User", users["username"])
    if st.button("Delete User"):
        users = users[users["username"] != remove_user]
        students = students[students["student_name"] != remove_user]
        marks = marks[marks["student"] != remove_user]
        attendance = attendance[attendance["student"] != remove_user]

        save_data(users, USERS_FILE)
        save_data(students, STUDENTS_FILE)
        save_data(marks, MARKS_FILE)
        save_data(attendance, ATTENDANCE_FILE)

        st.success("User Removed")

# ==========================
# TEACHER DASHBOARD
# ==========================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    users, students, marks, results, attendance = load_data()

    selected_class = st.selectbox("Select Class", CLASSES)

    class_students = students[students["class_level"] == selected_class]

    if class_students.empty:
        st.warning("No students in this class.")
        st.stop()

    selected_student = st.selectbox("Select Student", class_students["student_name"])
    term = st.selectbox("Select Term", TERMS)

    # =====================
    # ENTER MARKS
    # =====================
    st.subheader("✏️ Enter Marks")

    subject_marks = {}

    for subj in COMPULSORY:
        subject_marks[subj] = st.number_input(f"{subj}", 0, 100, 0)

    humanity = st.selectbox("Choose ONE Humanity", GROUP_HUMANITIES)
    humanity_mark = st.number_input(f"{humanity}", 0, 100, 0)

    tech = st.selectbox("Choose ONE (CRE or Physics)", GROUP_TECH)
    tech_mark = st.number_input(f"{tech}", 0, 100, 0)

    if st.button("Save Marks"):

        marks = marks[~(
            (marks["student"] == selected_student) &
            (marks["term"] == term)
        )]

        new_rows = []

        for subj, mark in subject_marks.items():
            new_rows.append([selected_student, selected_class, term, subj, mark])

        new_rows.append([selected_student, selected_class, term, humanity, humanity_mark])
        new_rows.append([selected_student, selected_class, term, tech, tech_mark])

        new_df = pd.DataFrame(new_rows, columns=marks.columns)

        marks = pd.concat([marks, new_df], ignore_index=True)

        save_data(marks, MARKS_FILE)

        st.success("Marks Saved Successfully")

    # =====================
    # ATTENDANCE ENTRY
    # =====================
    st.subheader("📋 Enter Attendance")

    days_present = st.number_input("Days Present", 0, 100, 0)
    total_days = st.number_input("Total Days", 1, 100, 1)

    if st.button("Save Attendance"):

        attendance = attendance[~(
            (attendance["student"] == selected_student) &
            (attendance["term"] == term)
        )]

        percent = (days_present / total_days) * 100

        attendance.loc[len(attendance)] = [
            selected_student,
            selected_class,
            term,
            days_present,
            total_days,
            round(percent,2)
        ]

        save_data(attendance, ATTENDANCE_FILE)

        st.success("Attendance Saved Successfully")

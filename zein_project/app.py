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
GROUP_3 = ["Business", "Agriculture", "Computer",
           "French", "German", "Arabic"]
GROUP_4 = ["Wood Technology", "Metal Work",
           "Building Construction", "Electricity"]

ALL_SUBJECTS = COMPULSORY + GROUP_1 + GROUP_2 + GROUP_3 + GROUP_4

# ==========================
# UTILITIES
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
# CREATE FILES
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"],
            [["admin", hash_password("1234"), "admin", ""]])
create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

# ==========================
# LOGIN
# ==========================
if "user" not in st.session_state:
    st.title("🎓Zein School Login")

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
# STUDENT DASHBOARD (AI ENABLED)
# ==========================
if role == "student":
    st.header("📊 Student AI Dashboard")

    student_name = user["username"]

    student_results = results[results["student"]==student_name]
    student_marks = marks[marks["student"]==student_name]

    if student_results.empty:
        st.warning("No results yet")
        st.stop()

    # ================= Trend Graph =================
    st.subheader("📈 Performance Trend")

    history = student_results.copy()
    history["term_order"] = history["term"].map(TERM_ORDER)
    history = history.sort_values("term_order")

    fig, ax = plt.subplots()
    ax.plot(history["term"], history["average"], marker='o')
    ax.set_ylabel("Average Score")
    ax.set_xlabel("Term")
    ax.set_title("Performance Over Time")
    st.pyplot(fig)

    # ================= Prediction =================
    if len(history) >= 2:
        X = np.arange(len(history)).reshape(-1,1)
        y = history["average"].values

        model = LinearRegression()
        model.fit(X,y)

        prediction = model.predict([[len(history)]])[0]
        prediction = max(0,min(100,prediction))

        st.subheader("🔮 Next Term Prediction")
        col1, col2 = st.columns(2)
        col1.metric("Predicted Average", round(prediction,2))
        col2.metric("Predicted Grade", grade(prediction))

    # ================= Weak Subject Detection =================
    st.subheader("📉 Weak Subject Analysis")

    latest_term = history.iloc[-1]["term"]
    latest_marks = student_marks[student_marks["term"]==latest_term]

    if not latest_marks.empty:
        weakest = latest_marks.sort_values("marks").iloc[0]
        strongest = latest_marks.sort_values("marks", ascending=False).iloc[0]

        st.error(f"Weakest Subject: {weakest['subject']} ({weakest['marks']}%)")
        st.success(f"Strongest Subject: {strongest['subject']} ({strongest['marks']}%)")

        # ================= AI Advice =================
        st.subheader("🤖 Zein AI Academic Advice")

        advice = ""

        if weakest["marks"] < 50:
            advice += f"Focus seriously on {weakest['subject']}. Consider extra practice and revision daily. "
        elif weakest["marks"] < 60:
            advice += f"Improve {weakest['subject']} by reviewing weak topics weekly. "

        if prediction >= 75:
            advice += "You are on a strong upward trend. Maintain consistency."
        elif prediction < 60:
            advice += "Overall performance is at risk. Increase study time and seek help from teachers."

        st.info(advice)

    # ================= Attendance =================
    st.subheader("📋 Attendance")
    student_att = attendance[attendance["student"]==student_name]
    if not student_att.empty:
        st.dataframe(student_att[["term","attendance_percent"]])


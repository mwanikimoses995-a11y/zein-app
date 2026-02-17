import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="School System", layout="wide")

# =====================================================
# FILES
# =====================================================
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"
RESULTS_FILE = "term_results.csv"

# =====================================================
# SUBJECT STRUCTURE
# =====================================================
COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry"]
HUMANITIES = ["History", "Geography"]
SCIENCE_OPTION = ["Physics", "CRE"]
TECH_OPTION = ["Business", "Agriculture", "French", "HomeScience", "Computer"]

# =====================================================
# PASSWORD HASH
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =====================================================
# CREATE FILES IF NOT EXIST
# =====================================================
def create_file(file, columns, data=None):
    if not os.path.exists(file):
        pd.DataFrame(data if data else [], columns=columns).to_csv(file, index=False)

create_file(USERS_FILE, ["username", "password", "role"],
            [["admin", hash_password("12345"), "admin"]])
create_file(STUDENTS_FILE, ["student_name"])
create_file(MARKS_FILE, ["student", "subject", "marks"])
create_file(ATTENDANCE_FILE, ["student", "attendance_percent"])
create_file(RESULTS_FILE, ["student", "total_marks", "average", "grade"])

# =====================================================
# LOAD DATA
# =====================================================
def load_all_data():
    return (
        pd.read_csv(USERS_FILE),
        pd.read_csv(STUDENTS_FILE),
        pd.read_csv(MARKS_FILE),
        pd.read_csv(ATTENDANCE_FILE),
        pd.read_csv(RESULTS_FILE),
    )

users, students, marks, attendance, results = load_all_data()

def save(df, file):
    df.to_csv(file, index=False)

# =====================================================
# GRADE FUNCTION
# =====================================================
def calculate_grade(mark):
    if mark >= 80: return "A"
    elif mark >= 70: return "B"
    elif mark >= 60: return "C"
    elif mark >= 50: return "D"
    else: return "E"

# =====================================================
# LOGIN
# =====================================================
if "user" not in st.session_state:
    st.title("🎓 School Portal Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        hashed = hash_password(password)
        match = users[(users.username == username) & (users.password == hashed)]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Wrong username or password")
    st.stop()

# =====================================================
# AFTER LOGIN
# =====================================================
user = st.session_state.user
role = user["role"]

st.sidebar.success(f"Logged in as {user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# =====================================================
# ADMIN PANEL
# =====================================================
if role == "admin":
    st.header("👨‍💼 Admin Panel")
    tab1, tab2 = st.tabs(["Add User", "Remove User"])

    with tab1:
        option = st.radio("Add", ["Student", "Teacher"])
        if option == "Student":
            name = st.text_input("Student Name")
            if st.button("Add Student"):
                username = name.replace(" ", "").lower()
                if username in users.username.values:
                    st.warning("User already exists")
                else:
                    new_user = pd.DataFrame([[username, hash_password("1234"), "student"]], columns=users.columns)
                    new_student = pd.DataFrame([[username]], columns=students.columns)
                    save(pd.concat([users, new_user]), USERS_FILE)
                    save(pd.concat([students, new_student]), STUDENTS_FILE)
                    st.success(f"Student {username} added with default password '1234'")
                    st.rerun()
        else:
            subject = st.selectbox("Subject", COMPULSORY + HUMANITIES + SCIENCE_OPTION + TECH_OPTION)
            number = st.number_input("Teacher Number", 1)
            if st.button("Add Teacher"):
                username = f"{subject.lower()}{int(number)}"
                if username in users.username.values:
                    st.warning("User exists")
                else:
                    new_user = pd.DataFrame([[username, hash_password("1234"), "teacher"]], columns=users.columns)
                    save(pd.concat([users, new_user]), USERS_FILE)
                    st.success(f"Teacher {username} added")
                    st.rerun()

    with tab2:
        removable = users[users.role != "admin"]
        if not removable.empty:
            selected_user = st.selectbox("Select user to remove", removable.username)
            if st.button("Delete User"):
                # Filtering out the user from all dataframes
                save(users[users.username != selected_user], USERS_FILE)
                save(students[students.student_name != selected_user], STUDENTS_FILE)
                save(marks[marks.student != selected_user], MARKS_FILE)
                save(attendance[attendance.student != selected_user], ATTENDANCE_FILE)
                save(results[results.student != selected_user], RESULTS_FILE)
                st.success(f"User {selected_user} deleted")
                st.rerun()
        else:
            st.info("No users available to remove.")

    st.subheader("Current Users")
    st.dataframe(users, use_container_width=True)

# =====================================================
# STUDENT PANEL
# =====================================================
elif role == "student":
    st.header(f"📊 Results for {user['username']}")
    student_name = user["username"]

    student_marks = marks[marks.student == student_name]
    student_result = results[results.student == student_name]
    student_att = attendance[attendance.student == student_name]

    col1, col2 = st.columns(2)

    with col1:
        if not student_marks.empty:
            st.subheader("Subject Marks")
            st.table(student_marks)
        else:
            st.info("No marks recorded yet.")

    with col2:
        if not student_marks.empty:
            st.subheader("Performance Trend")
            st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty or not student_att.empty:
        st.divider()
        c3, c4 = st.columns(2)
        with c3:
            if not student_result.empty:
                st.metric("Final Grade", student_result.iloc[0]['grade'])
                st.metric("Total Marks", student_result.iloc[0]['total_marks'])
        with c4:
            if not student_att.empty:
                st.metric("Attendance", f"{student_att.iloc[0]['attendance_percent']}%")

    # Prediction
    if len(student_marks) > 1:
        st.divider()
        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values
        model = LinearRegression()
        model.fit(X, y)
        prediction = model.predict([[len(y)]])[0]
        st.info(f"📈 Based on your current trend, your predicted next mark is: **{round(prediction, 1)}**")

# =====================================================
# TEACHER PANEL (Placeholder for logic if needed)
# =====================================================
elif role == "teacher":
    st.header("👩‍🏫 Teacher Dashboard")
    st.write(f"Subject: {user['username']}")
    st.info("Teacher mark entry logic can be implemented here.")

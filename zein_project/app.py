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
# PASSWORD HASH FUNCTION
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =====================================================
# CREATE FILES IF NOT EXIST
# =====================================================
def create_file(file, columns, data=[]):
    if not os.path.exists(file):
        pd.DataFrame(data, columns=columns).to_csv(file, index=False)

create_file(USERS_FILE, ["username", "password", "role"], [["admin", hash_password("12345"), "admin"]])
create_file(STUDENTS_FILE, ["student_name"])
create_file(MARKS_FILE, ["student", "subject", "marks"])
create_file(ATTENDANCE_FILE, ["student", "attendance_percent"])
create_file(RESULTS_FILE, ["student", "total_marks", "average", "grade"])

# =====================================================
# LOAD DATA
# =====================================================
users = pd.read_csv(USERS_FILE)
students = pd.read_csv(STUDENTS_FILE)
marks = pd.read_csv(MARKS_FILE)
attendance = pd.read_csv(ATTENDANCE_FILE)
results = pd.read_csv(RESULTS_FILE)

def save(df, file):
    df.to_csv(file, index=False)

# =====================================================
# GRADE CALCULATION
# =====================================================
def calculate_grade(mark):
    if mark >= 80:
        return "A"
    elif mark >= 70:
        return "B"
    elif mark >= 60:
        return "C"
    elif mark >= 50:
        return "D"
    else:
        return "E"

# =====================================================
# LOGIN + FORGOT PASSWORD
# =====================================================
if "user" not in st.session_state:

    st.title("🎓 School Portal Login")

    tab1, tab2 = st.tabs(["Login", "Forgot Password"])

    # ---------------- LOGIN ----------------
    with tab1:
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

    # ---------------- FORGOT PASSWORD ----------------
    with tab2:
        st.subheader("Security Question")
        reset_user = st.text_input("Enter your username")
        answer = st.text_input("Who is zein ?", type="password")

        if st.button("Reset Password"):
            if reset_user in users["username"].values:
                if answer.strip().lower() == "zeiniszein":
                    users.loc[users.username == reset_user, "password"] = hash_password("1234")
                    save(users, USERS_FILE)
                    st.success("Password reset to default: 1234")
                else:
                    st.error("Incorrect security answer")
            else:
                st.error("Username not found")

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
    st.header("👨‍💼 Admin Panel - Add Users")

    add_option = st.radio("Add", ["Student", "Teacher"])

    if add_option == "Student":
        student_name = st.text_input("Student Name")
        if st.button("Add Student"):
            if student_name.strip() != "":
                username = student_name.replace(" ", "").lower()
                if username in users.username.values:
                    st.warning("Student already exists")
                else:
                    users.loc[len(users)] = [username, hash_password("1234"), "student"]
                    save(users, USERS_FILE)
                    students.loc[len(students)] = [student_name]
                    save(students, STUDENTS_FILE)
                    st.success(f"Student {student_name} added with username '{username}' and password '1234'")
                    st.rerun()

    elif add_option == "Teacher":
        subject = st.selectbox("Select Subject", COMPULSORY + HUMANITIES + SCIENCE_OPTION + TECH_OPTION)
        teacher_number = st.number_input("Teacher Number", min_value=1, step=1)
        if st.button("Add Teacher"):
            username = f"{subject.lower()}{int(teacher_number)}"
            if username in users.username.values:
                st.warning("Teacher account already exists")
            else:
                users.loc[len(users)] = [username, hash_password("1234"), "teacher"]
                save(users, USERS_FILE)
                st.success(f"Teacher account created: {username}, default password '1234'")
                st.rerun()

    st.subheader("Existing Users")
    st.dataframe(users)

# =====================================================
# TEACHER PANEL
# =====================================================
elif role == "teacher":
    st.header("📋 Teacher Dashboard")

    if students.empty:
        st.warning("No students registered.")
    else:
        selected_student = st.selectbox("Select Student", students["student_name"])

        # SUBJECT SELECTION RULES
        human_choice = st.selectbox("Choose ONE: History or Geography", HUMANITIES)
        science_choice = st.selectbox("Choose ONE: Physics or CRE", SCIENCE_OPTION)
        tech_choice = st.selectbox(
            "Choose ONE: Business, Agriculture, French, HomeScience, Computer", TECH_OPTION
        )

        selected_subjects = COMPULSORY + [human_choice, science_choice, tech_choice]

        st.subheader("✏️ Enter / Edit Marks")
        for subject in selected_subjects:
            existing = marks[(marks.student == selected_student) & (marks.subject == subject)]
            current_mark = int(existing.marks.values[0]) if not existing.empty else 0

            new_mark = st.number_input(
                f"{subject}", 0, 100, current_mark, key=f"{selected_student}_{subject}"
            )

            if not existing.empty:
                marks.loc[(marks.student == selected_student) & (marks.subject == subject), "marks"] = new_mark
            else:
                marks.loc[len(marks)] = [selected_student, subject, new_mark]

        if st.button("Save Marks"):
            save(marks, MARKS_FILE)
            st.success("Marks saved successfully")
            st.rerun()

        # ATTENDANCE
        st.subheader("📅 Attendance")
        existing_att = attendance[attendance.student == selected_student]
        current_att = int(existing_att.attendance_percent.values[0]) if not existing_att.empty else 0

        att_value = st.number_input("Attendance %", 0, 100, current_att)

        if st.button("Save Attendance"):
            if not existing_att.empty:
                attendance.loc[attendance.student == selected_student, "attendance_percent"] = att_value
            else:
                attendance.loc[len(attendance)] = [selected_student, att_value]
            save(attendance, ATTENDANCE_FILE)
            st.success("Attendance updated")
            st.rerun()

        # TERM RESULTS
        st.subheader("📊 Term Results")
        student_marks = marks[marks.student == selected_student]
        if not student_marks.empty:
            total = student_marks.marks.sum()
            average = round(student_marks.marks.mean(), 2)
            grade = calculate_grade(average)

            st.write(f"Total Marks: {total}")
            st.write(f"Average: {average}")
            st.write(f"Grade: {grade}")

            if st.button("Save Term Results"):
                results = results[results.student != selected_student]
                results.loc[len(results)] = [selected_student, total, average, grade]
                save(results, RESULTS_FILE)
                st.success("Term results saved")

        # =====================================================
        # Linear Regression Prediction
        # =====================================================
        st.subheader("🤖 Predicted Next Marks")
        if len(student_marks) > 1:
            X = np.arange(len(student_marks)).reshape(-1, 1)
            y = student_marks["marks"].values
            model = LinearRegression()
            model.fit(X, y)
            next_mark = model.predict([[len(y)]])[0]
            st.success(f"Predicted next mark (based on trend): {round(next_mark, 1)}")
        else:
            st.info("Need more marks to predict performance.")

# =====================================================
# STUDENT VIEW
# =====================================================
elif role == "student":
    st.header("📊 My Results")

    student_name = user["username"]
    student_marks = marks[marks.student == student_name]
    student_result = results[results.student == student_name]
    student_att = attendance[attendance.student == student_name]

    if not student_marks.empty:
        st.subheader("Marks")
        st.dataframe(student_marks)
        st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty:
        st.subheader("Term Summary")
        st.write(student_result)

    if not student_att.empty:
        st.subheader("Attendance")
        st.write(student_att)

    # =====================================================
    # Linear Regression Prediction
    # =====================================================
    st.subheader("🤖 Predicted Next Marks")
    if len(student_marks) > 1:
        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values
        model = LinearRegression()
        model.fit(X, y)
        next_mark = model.predict([[len(y)]])[0]
        st.success(f"Predicted next mark (based on trend): {round(next_mark, 1)}")
    else:
        st.info("Need more marks to predict performance.")

import streamlit as st
import pandas as pd
import os
import hashlib

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
if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        ["admin", hash_password("12345"), "admin"],
        ["teacher1", hash_password("1234"), "teacher"]
    ], columns=["username", "password", "role"]).to_csv(USERS_FILE, index=False)

if not os.path.exists(STUDENTS_FILE):
    pd.DataFrame(columns=["student_name"]).to_csv(STUDENTS_FILE, index=False)

if not os.path.exists(MARKS_FILE):
    pd.DataFrame(columns=["student", "subject", "marks"]).to_csv(MARKS_FILE, index=False)

if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=["student", "attendance_percent"]).to_csv(ATTENDANCE_FILE, index=False)

if not os.path.exists(RESULTS_FILE):
    pd.DataFrame(columns=["student", "total_marks", "average"]).to_csv(RESULTS_FILE, index=False)

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

            match = users[
                (users.username == username) &
                (users.password == hashed)
            ]

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
                    users.loc[users.username == reset_user,
                              "password"] = hash_password("1234")
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

    st.header("👨‍💼 Admin Panel")

    new_student = st.text_input("Add Student Name")

    if st.button("Add Student"):
        if new_student.strip() != "":
            students.loc[len(students)] = [new_student.strip()]
            save(students, STUDENTS_FILE)
            st.success("Student added")
            st.rerun()

    st.subheader("Student List")
    st.dataframe(students)

# =====================================================
# TEACHER PANEL
# =====================================================
elif role == "teacher":

    st.header("📋 Teacher Dashboard")

    if students.empty:
        st.warning("No students registered.")
    else:

        selected_student = st.selectbox(
            "Select Student", students["student_name"])

        # SUBJECT SELECTION RULES
        human_choice = st.selectbox(
            "Choose ONE: History or Geography", HUMANITIES)

        science_choice = st.selectbox(
            "Choose ONE: Physics or CRE", SCIENCE_OPTION)

        tech_choice = st.selectbox(
            "Choose ONE: Business, Agriculture, French, HomeScience or Computer", TECH_OPTION)

        selected_subjects = COMPULSORY + \
            [human_choice, science_choice, tech_choice]

        st.subheader("✏️ Enter / Edit Marks")

        for subject in selected_subjects:

            existing = marks[(marks.student == selected_student) &
                             (marks.subject == subject)]

            current_mark = int(existing.marks.values[0]) if not existing.empty else 0

            new_mark = st.number_input(
                f"{subject}", 0, 100, current_mark, key=f"{selected_student}_{subject}")

            if not existing.empty:
                marks.loc[(marks.student == selected_student) &
                          (marks.subject == subject), "marks"] = new_mark
            else:
                marks.loc[len(marks)] = [
                    selected_student, subject, new_mark]

        if st.button("Save Marks"):
            save(marks, MARKS_FILE)
            st.success("Marks saved successfully")
            st.rerun()

        # ATTENDANCE
        st.subheader("📅 Attendance")

        existing_att = attendance[attendance.student == selected_student]
        current_att = int(existing_att.attendance_percent.values[0]) if not existing_att.empty else 0

        att_value = st.number_input(
            "Attendance Percentage", 0, 100, current_att)

        if st.button("Save Attendance"):
            if not existing_att.empty:
                attendance.loc[attendance.student ==
                               selected_student, "attendance_percent"] = att_value
            else:
                attendance.loc[len(attendance)] = [
                    selected_student, att_value]
            save(attendance, ATTENDANCE_FILE)
            st.success("Attendance updated")
            st.rerun()

        # TERM RESULTS
        st.subheader("📊 Term Results")

        student_marks = marks[marks.student == selected_student]

        if not student_marks.empty:
            total = student_marks.marks.sum()
            average = round(student_marks.marks.mean(), 2)

            st.write(f"Total Marks: {total}")
            st.write(f"Average: {average}")

            if st.button("Save Term Results"):
                results = results[results.student != selected_student]
                results.loc[len(results)] = [
                    selected_student, total, average]
                save(results, RESULTS_FILE)
                st.success("Term results saved")

            st.dataframe(student_marks)

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
        st.dataframe(student_marks)
        st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty:
        st.subheader("Term Summary")
        st.write(student_result)

    if not student_att.empty:
        st.subheader("Attendance")
        st.write(student_att)

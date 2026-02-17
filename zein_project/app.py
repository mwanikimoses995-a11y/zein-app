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

ALL_SUBJECTS = COMPULSORY + HUMANITIES + SCIENCE_OPTION + TECH_OPTION

# =====================================================
# PASSWORD HASH
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# =====================================================
# CREATE FILES
# =====================================================
def create_file(file, columns, data=None):
    if not os.path.exists(file):
        pd.DataFrame(data if data else [], columns=columns).to_csv(file, index=False)

create_file(
    USERS_FILE,
    ["username", "password", "role", "subject"],
    [["admin", hash_password("12345"), "admin", ""]],
)

create_file(STUDENTS_FILE, ["student_name"])
create_file(MARKS_FILE, ["student", "subject", "marks"])
create_file(ATTENDANCE_FILE, ["student", "attendance_percent"])
create_file(RESULTS_FILE, ["student", "total_marks", "average", "grade"])

# =====================================================
# LOAD & SAVE
# =====================================================
def load_all():
    return (
        pd.read_csv(USERS_FILE),
        pd.read_csv(STUDENTS_FILE),
        pd.read_csv(MARKS_FILE),
        pd.read_csv(ATTENDANCE_FILE),
        pd.read_csv(RESULTS_FILE),
    )

def save(df, file):
    df.to_csv(file, index=False)

# =====================================================
# GRADE FUNCTION
# =====================================================
def calculate_grade(avg):
    if avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "E"

# =====================================================
# LOAD DATA
# =====================================================
users, students, marks, attendance, results = load_all()

# =====================================================
# LOGIN + FORGOT PASSWORD
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

    st.divider()
    st.subheader("Forgot Password")

    fp_username = st.text_input("Enter Username for Reset")

    if st.button("Reset Password"):
        if fp_username in users.username.values:

            answer = st.text_input("Security Question: Who is zein?")

            if st.button("Submit Answer"):
                if answer.strip().lower() == "zein is zein":
                    users.loc[users.username == fp_username, "password"] = hash_password("1234")
                    save(users, USERS_FILE)
                    st.success("Password reset to default: 1234")
                else:
                    st.error("Wrong answer.")
        else:
            st.error("Username not found.")

    st.stop()

# =====================================================
# SESSION
# =====================================================
user = st.session_state.user
role = user["role"]

st.sidebar.success(f"Logged in as {user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

users, students, marks, attendance, results = load_all()

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
                    st.warning("User exists")
                else:
                    new_user = pd.DataFrame(
                        [[username, hash_password("1234"), "student", ""]],
                        columns=users.columns,
                    )
                    new_student = pd.DataFrame([[username]], columns=students.columns)

                    save(pd.concat([users, new_user], ignore_index=True), USERS_FILE)
                    save(pd.concat([students, new_student], ignore_index=True), STUDENTS_FILE)
                    st.success("Student added")
                    st.rerun()

        else:
            subject = st.selectbox("Assign Subject (optional)", ALL_SUBJECTS)
            number = st.number_input("Teacher Number", min_value=1, step=1)

            if st.button("Add Teacher"):
                username = f"{subject.lower()}{int(number)}"
                if username in users.username.values:
                    st.warning("User exists")
                else:
                    new_user = pd.DataFrame(
                        [[username, hash_password("1234"), "teacher", subject]],
                        columns=users.columns,
                    )
                    save(pd.concat([users, new_user], ignore_index=True), USERS_FILE)
                    st.success("Teacher added")
                    st.rerun()

    with tab2:
        removable = users[users.role != "admin"]
        selected = st.selectbox("Select user", removable.username)

        if st.button("Delete"):
            save(users[users.username != selected], USERS_FILE)
            save(students[students.student_name != selected], STUDENTS_FILE)
            save(marks[marks.student != selected], MARKS_FILE)
            save(attendance[attendance.student != selected], ATTENDANCE_FILE)
            save(results[results.student != selected], RESULTS_FILE)
            st.success("User removed")
            st.rerun()

    st.subheader("All Users")
    st.dataframe(users)

# =====================================================
# TEACHER PANEL (UNLOCKED SUBJECTS)
# =====================================================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    st.subheader("Enter Marks")

    if students.empty:
        st.warning("No students available.")
    else:
        selected_student = st.selectbox("Select Student", students["student_name"])
        selected_subject = st.selectbox("Select Subject", ALL_SUBJECTS)
        mark = st.number_input("Enter Marks (0-100)", min_value=0, max_value=100)

        if st.button("Save Marks"):

            marks = marks[
                ~((marks.student == selected_student) &
                  (marks.subject == selected_subject))
            ]

            new_mark = pd.DataFrame(
                [[selected_student, selected_subject, mark]],
                columns=marks.columns
            )

            marks = pd.concat([marks, new_mark], ignore_index=True)
            save(marks, MARKS_FILE)

            student_marks = marks[marks.student == selected_student]
            total = student_marks["marks"].sum()
            average = student_marks["marks"].mean()
            grade = calculate_grade(average)

            results = results[results.student != selected_student]

            new_result = pd.DataFrame(
                [[selected_student, total, round(average, 2), grade]],
                columns=results.columns
            )

            results = pd.concat([results, new_result], ignore_index=True)
            save(results, RESULTS_FILE)

            st.success("Marks saved & results updated ✅")
            st.rerun()

    st.divider()
    st.subheader("Enter Attendance")

    selected_student_att = st.selectbox("Select Student for Attendance", students["student_name"])
    attendance_percent = st.number_input("Attendance %", min_value=0, max_value=100)

    if st.button("Save Attendance"):
        attendance = attendance[attendance.student != selected_student_att]
        new_att = pd.DataFrame(
            [[selected_student_att, attendance_percent]],
            columns=attendance.columns
        )
        attendance = pd.concat([attendance, new_att], ignore_index=True)
        save(attendance, ATTENDANCE_FILE)
        st.success("Attendance saved ✅")
        st.rerun()

# =====================================================
# STUDENT PANEL
# =====================================================
elif role == "student":

    st.header(f"📊 Results for {user['username']}")

    student_name = user["username"]

    student_marks = marks[marks.student == student_name]
    student_result = results[results.student == student_name]
    student_att = attendance[attendance.student == student_name]

    if not student_marks.empty:
        st.subheader("Subject Marks")
        st.table(student_marks)
        st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty:
        st.metric("Total Marks", student_result.iloc[0]["total_marks"])
        st.metric("Average", student_result.iloc[0]["average"])
        st.metric("Grade", student_result.iloc[0]["grade"])

    if not student_att.empty:
        st.metric("Attendance", f"{student_att.iloc[0]['attendance_percent']}%")

    # Prediction
    if len(student_marks) > 1:
        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values
        model = LinearRegression()
        model.fit(X, y)
        prediction = model.predict([[len(y)]])[0]
        st.info(f"📈 Predicted next mark: {round(prediction,1)}")

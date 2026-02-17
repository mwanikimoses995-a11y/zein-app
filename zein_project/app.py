import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from sklearn.linear_model import LinearRegression
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

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
def load_data():
    return (
        pd.read_csv(USERS_FILE),
        pd.read_csv(STUDENTS_FILE),
        pd.read_csv(MARKS_FILE),
        pd.read_csv(ATTENDANCE_FILE),
        pd.read_csv(RESULTS_FILE),
    )

users, students, marks, attendance, results = load_data()

def save(df, file):
    df.to_csv(file, index=False)

# =====================================================
# GRADE FUNCTION
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
# PDF GENERATOR
# =====================================================
def generate_pdf(student, student_marks, student_result, student_att):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    y = height - 40
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, y, "STUDENT REPORT")
    y -= 40

    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Student: {student}")
    y -= 30

    c.drawString(50, y, "Marks:")
    y -= 20

    for _, row in student_marks.iterrows():
        c.drawString(60, y, f"{row['subject']} : {row['marks']}")
        y -= 20

    y -= 10
    if not student_result.empty:
        res = student_result.iloc[0]
        c.drawString(50, y, f"Total: {res['total_marks']}")
        y -= 20
        c.drawString(50, y, f"Average: {res['average']}")
        y -= 20
        c.drawString(50, y, f"Grade: {res['grade']}")
        y -= 20

    if not student_att.empty:
        c.drawString(50, y, f"Attendance: {student_att.iloc[0]['attendance_percent']}%")

    c.save()
    buffer.seek(0)
    return buffer

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

    # ---------------- ADD USER ----------------
    with tab1:
        option = st.radio("Add", ["Student", "Teacher"])

        if option == "Student":
            name = st.text_input("Student Name")
            if st.button("Add Student"):
                username = name.replace(" ", "").lower()
                if username in users.username.values:
                    st.warning("User already exists")
                else:
                    users.loc[len(users)] = [username, hash_password("1234"), "student"]
                    students.loc[len(students)] = [username]
                    save(users, USERS_FILE)
                    save(students, STUDENTS_FILE)
                    st.success("Student added")

        else:
            subject = st.selectbox("Subject", COMPULSORY + HUMANITIES + SCIENCE_OPTION + TECH_OPTION)
            number = st.number_input("Teacher Number", 1)
            if st.button("Add Teacher"):
                username = f"{subject.lower()}{int(number)}"
                if username in users.username.values:
                    st.warning("User exists")
                else:
                    users.loc[len(users)] = [username, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success("Teacher added")

    # ---------------- REMOVE USER ----------------
    with tab2:
        removable = users[users.role != "admin"]
        selected_user = st.selectbox("Select user to remove", removable.username)

        if st.button("Delete User"):
            users.drop(users[users.username == selected_user].index, inplace=True)
            students.drop(students[students.student_name == selected_user].index, inplace=True)
            marks.drop(marks[marks.student == selected_user].index, inplace=True)
            attendance.drop(attendance[attendance.student == selected_user].index, inplace=True)
            results.drop(results[results.student == selected_user].index, inplace=True)

            save(users, USERS_FILE)
            save(students, STUDENTS_FILE)
            save(marks, MARKS_FILE)
            save(attendance, ATTENDANCE_FILE)
            save(results, RESULTS_FILE)

            st.success("User deleted successfully")
            st.rerun()

    st.dataframe(users)

# =====================================================
# STUDENT PANEL
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
        st.write(student_result)

    if not student_att.empty:
        st.write(student_att)

    # PDF Download
    if not student_marks.empty:
        pdf = generate_pdf(student_name, student_marks, student_result, student_att)
        st.download_button(
            label="📥 Download Report as PDF",
            data=pdf,
            file_name=f"{student_name}_report.pdf",
            mime="application/pdf"
        )

    # Prediction
    if len(student_marks) > 1:
        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values
        model = LinearRegression()
        model.fit(X, y)
        prediction = model.predict([[len(y)]])[0]
        st.success(f"Predicted Next Mark: {round(prediction,1)}")

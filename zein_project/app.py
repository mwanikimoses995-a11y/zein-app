import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt

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
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4"]
SUBJECTS = ["English", "Mathematics", "Kiswahili", "Biology", "Chemistry", "Physics"]

# ==========================
# UTILITIES
# ==========================
def hash_password(p): 
    return hashlib.sha256(p.encode()).hexdigest()

def create_file(file, cols, default=None):
    if not os.path.exists(file):
        pd.DataFrame(default if default else [], columns=cols).to_csv(file, index=False)

def save(df, file): 
    df.to_csv(file, index=False)

def grade(avg):
    if avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    return "E"

# ==========================
# CREATE FILES
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"],
            [["admin", hash_password("1234"), "admin", ""]])
create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","attendance_percent"])

users = pd.read_csv(USERS_FILE)
students = pd.read_csv(STUDENTS_FILE)
marks = pd.read_csv(MARKS_FILE)
results = pd.read_csv(RESULTS_FILE)
attendance = pd.read_csv(ATTENDANCE_FILE)

# ==========================
# LOGIN
# ==========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        m = users[(users.username==u)&(users.password==hash_password(p))]
        if not m.empty:
            st.session_state.user = m.iloc[0].to_dict()
            st.experimental_rerun()
        else:
            st.error("Invalid login")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 {user['username']} ({role})")
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.experimental_rerun()

# ==========================
# STUDENT DASHBOARD
# ==========================
if role == "student":
    st.header("📊 Student Dashboard")

    name = user["username"]
    my_results = results[results.student == name]
    my_att = attendance[attendance.student == name]

    if my_results.empty:
        st.warning("No results yet")
        st.stop()

    st.subheader("📘 Term Results")
    st.dataframe(my_results)

    st.subheader("📋 Attendance")
    st.dataframe(my_att)

    merged = pd.merge(my_results, my_att, on=["student","class_level","term"], how="inner")

    if len(merged) > 1:
        corr = merged["attendance_percent"].corr(merged["average"])

        st.subheader("📈 Attendance vs Performance")
        fig, ax = plt.subplots()
        ax.scatter(merged["attendance_percent"], merged["average"])
        ax.set_xlabel("Attendance %")
        ax.set_ylabel("Average Marks")
        ax.set_title(f"Correlation: {corr:.2f}")
        st.pyplot(fig)

# ==========================
# ADMIN DASHBOARD
# ==========================
elif role == "admin":
    st.header("🛠 Admin Dashboard")

    name = st.text_input("Student Name")
    cls = st.selectbox("Class", CLASSES)

    if st.button("Add Student"):
        if name not in users.username.values:
            students.loc[len(students)] = [name, cls]
            users.loc[len(users)] = [name, hash_password("1234"), "student", ""]
            save(students, STUDENTS_FILE)
            save(users, USERS_FILE)
            st.success("Student added")

    st.subheader("👥 Users")
    st.dataframe(users)

# ==========================
# TEACHER DASHBOARD
# ==========================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    cls = st.selectbox("Class", CLASSES)
    term = st.selectbox("Term", TERMS)

    class_students = students[students.class_level == cls]
    if class_students.empty:
        st.warning("No students")
        st.stop()

    # ==========================
    # MARKS ENTRY
    # ==========================
    table = []
    for s in class_students.student_name:
        row = {"Student": s}
        for sub in SUBJECTS:
            ex = marks[(marks.student==s)&(marks.term==term)&(marks.subject==sub)]
            row[sub] = int(ex.marks.iloc[0]) if not ex.empty else 0
        table.append(row)

    df = pd.DataFrame(table)
    edited = st.data_editor(df, num_rows="fixed")

    # ==========================
    # ATTENDANCE ENTRY
    # ==========================
    st.subheader("📋 Attendance (%)")

    att_data = {}
    for s in class_students.student_name:
        ex = attendance[(attendance.student==s)&(attendance.term==term)]
        att_data[s] = st.number_input(
            f"{s}", 0, 100, 
            int(ex.attendance_percent.iloc[0]) if not ex.empty else 0
        )

    # ==========================
    # SAVE ALL
    # ==========================
    if st.button("💾 Save Marks & Attendance"):

        marks.drop(marks[(marks.class_level==cls)&(marks.term==term)].index, inplace=True)
        results.drop(results[(results.class_level==cls)&(results.term==term)].index, inplace=True)
        attendance.drop(attendance[(attendance.class_level==cls)&(attendance.term==term)].index, inplace=True)

        for _, r in edited.iterrows():
            scores = []
            for sub in SUBJECTS:
                marks.loc[len(marks)] = [r["Student"], cls, term, sub, r[sub]]
                scores.append(r[sub])

            avg = sum(scores)/len(scores)
            results.loc[len(results)] = [
                r["Student"], cls, term, sum(scores), round(avg,2), grade(avg)
            ]

            attendance.loc[len(attendance)] = [
                r["Student"], cls, term, att_data[r["Student"]]
            ]

        save(marks, MARKS_FILE)
        save(results, RESULTS_FILE)
        save(attendance, ATTENDANCE_FILE)

        st.success("Saved successfully")

    # ==========================
    # CLASS CORRELATION
    # ==========================
    merged = pd.merge(
        results[(results.class_level==cls)&(results.term==term)],
        attendance[(attendance.class_level==cls)&(attendance.term==term)],
        on=["student","class_level","term"]
    )

    if len(merged) > 1:
        corr = merged["attendance_percent"].corr(merged["average"])

        st.subheader("📊 Class Attendance–Performance Correlation")
        fig, ax = plt.subplots()
        ax.scatter(merged["attendance_percent"], merged["average"])
        ax.set_xlabel("Attendance %")
        ax.set_ylabel("Average Marks")
        ax.set_title(f"Correlation: {corr:.2f}")
        st.pyplot(fig)

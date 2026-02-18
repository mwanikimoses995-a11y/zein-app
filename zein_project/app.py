import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Advanced School ERP", layout="wide")

# =====================================================
# FILES
# =====================================================
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
RESULTS_FILE = "results.csv"
ATTENDANCE_FILE = "attendance.csv"

# =====================================================
# CONFIG
# =====================================================
TERMS = ["Term 1", "Term 2", "Term 3"]
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4"]

COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
GROUP_1 = ["CRE", "Physics"]
GROUP_2 = ["History", "Geography"]
GROUP_3 = ["Business", "Agriculture", "French", "HomeScience", "Computer"]

ALL_SUBJECTS = COMPULSORY + GROUP_1 + GROUP_2 + GROUP_3

# =====================================================
# UTILITIES
# =====================================================
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_file(file, columns, default=None):
    if not os.path.exists(file):
        pd.DataFrame(default if default else [], columns=columns).to_csv(file, index=False)

def save(df, file):
    df.to_csv(file, index=False)

def load():
    return (
        pd.read_csv(USERS_FILE),
        pd.read_csv(STUDENTS_FILE),
        pd.read_csv(MARKS_FILE),
        pd.read_csv(RESULTS_FILE),
        pd.read_csv(ATTENDANCE_FILE)
    )

def grade(avg):
    if avg >= 80: return "A"
    elif avg >= 70: return "B"
    elif avg >= 60: return "C"
    elif avg >= 50: return "D"
    else: return "E"

# =====================================================
# INITIALIZE FILES
# =====================================================
create_file(USERS_FILE, ["username","password","role","subject"],
            [["admin", hash_password("12345"), "admin", ""]])

create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

users, students, marks, results, attendance = load()

# =====================================================
# LOGIN
# =====================================================
if "user" not in st.session_state:

    st.title("🎓 Advanced School ERP Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        match = users[(users.username==u) & (users.password==hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.success(f"{user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

users, students, marks, results, attendance = load()

# =====================================================
# ADMIN DASHBOARD
# =====================================================
if role == "admin":

    st.header("🛠 Admin Dashboard")

    # ----- Add Student -----
    st.subheader("Add Student")
    name = st.text_input("Student Name")
    class_level = st.selectbox("Class Level", CLASSES)

    if st.button("Add Student"):
        if name in students.student_name.values:
            st.error("Student exists")
        else:
            students = pd.concat([students, pd.DataFrame([{
                "student_name": name,
                "class_level": class_level
            }])])
            save(students, STUDENTS_FILE)
            st.success("Student added")
            st.rerun()

# =====================================================
# TEACHER DASHBOARD
# =====================================================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    if students.empty:
        st.warning("No students found")
        st.stop()

    selected_class = st.selectbox("Select Class", CLASSES)
    selected_term = st.selectbox("Select Term", TERMS)

    class_students = students[students.class_level==selected_class]

    if class_students.empty:
        st.warning("No students in this class")
        st.stop()

    selected_student = st.selectbox("Select Student", class_students.student_name)

    tab1, tab2 = st.tabs(["Marks Entry","Attendance"])

    # ================= MARKS =================
    with tab1:

        student_data = []

        for subject in COMPULSORY:
            m = st.number_input(f"{subject}",0,100,key=f"{subject}")
            student_data.append((subject,m))

        g1 = st.radio("Group 1", GROUP_1)
        student_data.append((g1, st.number_input(f"{g1}",0,100)))

        g2 = st.radio("Group 2", GROUP_2)
        student_data.append((g2, st.number_input(f"{g2}",0,100)))

        g3 = st.radio("Group 3", GROUP_3)
        student_data.append((g3, st.number_input(f"{g3}",0,100)))

        if st.button("Save Marks"):

            marks = marks[~((marks.student==selected_student)&
                            (marks.term==selected_term)&
                            (marks.class_level==selected_class))]

            df = pd.DataFrame(student_data, columns=["subject","marks"])
            df.insert(0,"term",selected_term)
            df.insert(0,"class_level",selected_class)
            df.insert(0,"student",selected_student)

            marks = pd.concat([marks,df])
            save(marks, MARKS_FILE)

            total = df.marks.sum()
            avg = df.marks.mean()

            # Remove old result
            results = results[~((results.student==selected_student)&
                                (results.term==selected_term)&
                                (results.class_level==selected_class))]

            results = pd.concat([results,pd.DataFrame([{
                "student":selected_student,
                "class_level":selected_class,
                "term":selected_term,
                "total":total,
                "average":round(avg,2),
                "grade":grade(avg),
                "rank":0
            }])])

            # ===== RANKING SYSTEM =====
            term_results = results[(results.class_level==selected_class)&
                                   (results.term==selected_term)]

            term_results = term_results.sort_values("average", ascending=False)
            term_results["rank"] = range(1, len(term_results)+1)

            results.update(term_results)
            save(results, RESULTS_FILE)

            st.success("Marks saved & ranking updated")
            st.rerun()

    # ================= ATTENDANCE =================
    with tab2:

        total_days = st.number_input("Total Days",1,365,100)
        present = st.number_input("Days Present",0,total_days)

        if st.button("Save Attendance"):

            percent = round((present/total_days)*100,2)

            attendance = attendance[~((attendance.student==selected_student)&
                                       (attendance.term==selected_term)&
                                       (attendance.class_level==selected_class))]

            attendance = pd.concat([attendance,pd.DataFrame([{
                "student":selected_student,
                "class_level":selected_class,
                "term":selected_term,
                "days_present":present,
                "total_days":total_days,
                "attendance_percent":percent
            }])])

            save(attendance, ATTENDANCE_FILE)
            st.success("Attendance saved")
            st.rerun()

# =====================================================
# STUDENT DASHBOARD
# =====================================================
elif role == "student":

    st.header("📊 Student Dashboard")

    student_name = user["username"]

    student_results = results[results.student==student_name]
    student_marks = marks[marks.student==student_name]

    if student_results.empty:
        st.warning("No results yet")
        st.stop()

    selected_term = st.selectbox("Select Term", student_results.term.unique())

    term_data = student_results[student_results.term==selected_term]

    st.metric("Average", term_data.iloc[0]["average"])
    st.metric("Grade", term_data.iloc[0]["grade"])
    st.metric("Rank in Class", int(term_data.iloc[0]["rank"]))

    # ===== AI PREDICTION BASED ON HISTORY =====
    if len(student_results) >= 2:

        history = student_results.sort_values("term")
        X = np.arange(len(history)).reshape(-1,1)
        y = history.average.values

        model = LinearRegression()
        model.fit(X,y)

        future_index = [[len(history)]]
        prediction = model.predict(future_index)[0]

        st.info(f"🤖 Predicted Next Term Average: {round(prediction,2)}")
        st.info(f"Predicted Grade: {grade(prediction)}")

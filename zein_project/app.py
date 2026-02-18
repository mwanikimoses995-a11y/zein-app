import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Advanced School ERP", layout="wide")

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
# SUBJECTS (UPDATED)
# ==========================
COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]

GROUP_1 = ["Physics", "CRE", "IRE", "HRE"]  # Sciences & Religious
GROUP_2 = ["History", "Geography"]          # Humanities
GROUP_3 = ["Business", "Agriculture", "Computer",
           "French", "German", "Arabic"]    # Languages
GROUP_4 = ["Wood Technology", "Metal Work",
           "Building Construction", "Electricity"]  # Technical

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

def safe_columns(df, required_cols):
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
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
# INITIAL FILES
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
    st.title("🎓 Advanced School ERP Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        users, students, marks, results, attendance = load()
        match = users[(users["username"]==u) & (users["password"]==hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.success("Login successful")
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

users, students, marks, results, attendance = load()
user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 {user['username']} ({role})")
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# ==========================
# ADMIN
# ==========================
if role == "admin":
    st.header("Admin Dashboard")

    name = st.text_input("Student Name").strip()
    class_level = st.selectbox("Class", CLASSES)

    if st.button("Add Student"):
        if name and name not in students["student_name"].values:
            students = pd.concat([students, pd.DataFrame([{
                "student_name": name,
                "class_level": class_level
            }])], ignore_index=True)
            save(students, STUDENTS_FILE)

            users = pd.concat([users, pd.DataFrame([{
                "username": name,
                "password": hash_password("1234"),
                "role": "student",
                "subject": ""
            }])], ignore_index=True)
            save(users, USERS_FILE)

            st.success("Student added")
            st.rerun()
        else:
            st.error("Student exists or invalid")

# ==========================
# TEACHER
# ==========================
elif role == "teacher":
    st.header("Teacher Dashboard")

    selected_class = st.selectbox("Class", CLASSES)
    selected_term = st.selectbox("Term", TERMS)

    class_students = students[students["class_level"]==selected_class]

    if class_students.empty:
        st.warning("No students found")
        st.stop()

    selected_student = st.selectbox("Student", class_students["student_name"])

    # -------- MARKS ----------
    st.subheader("Enter Marks")

    student_data = []

    for subject in COMPULSORY:
        m = st.number_input(subject, 0, 100,
                            key=f"{subject}_{selected_student}_{selected_term}")
        student_data.append((subject, m))

    for group, subjects in {
        "Group 1": GROUP_1,
        "Group 2": GROUP_2,
        "Group 3": GROUP_3,
        "Group 4": GROUP_4
    }.items():
        st.write(f"**{group} (Select One)**")
        s = st.radio(group, subjects,
                     key=f"{group}_{selected_student}_{selected_term}")
        m = st.number_input(f"{s}", 0, 100,
                            key=f"{s}_{selected_student}_{selected_term}")
        student_data.append((s, m))

    if st.button("Save Marks"):
        marks = marks[~(
            (marks["student"]==selected_student) &
            (marks["term"]==selected_term) &
            (marks["class_level"]==selected_class)
        )]

        df = pd.DataFrame(student_data, columns=["subject","marks"])
        df.insert(0,"term",selected_term)
        df.insert(0,"class_level",selected_class)
        df.insert(0,"student",selected_student)

        marks = pd.concat([marks,df], ignore_index=True)
        save(marks, MARKS_FILE)

        total = df["marks"].sum()
        avg = df["marks"].mean()

        results = results[~(
            (results["student"]==selected_student) &
            (results["term"]==selected_term) &
            (results["class_level"]==selected_class)
        )]

        results = pd.concat([results, pd.DataFrame([{
            "student": selected_student,
            "class_level": selected_class,
            "term": selected_term,
            "total": total,
            "average": round(avg,2),
            "grade": grade(avg),
            "rank": 0
        }])], ignore_index=True)

        term_results = results[
            (results["class_level"]==selected_class) &
            (results["term"]==selected_term)
        ].sort_values("average", ascending=False).reset_index(drop=True)

        term_results["rank"] = range(1,len(term_results)+1)

        results = results[~(
            (results["class_level"]==selected_class) &
            (results["term"]==selected_term)
        )]

        results = pd.concat([results, term_results], ignore_index=True)
        save(results, RESULTS_FILE)

        st.success("Marks saved & ranking updated")
        st.rerun()

    # -------- ATTENDANCE ----------
    st.subheader("Class Attendance")

    total_days = st.number_input("Total Days in Term", 1, 365, 90)
    attendance_data = []

    for student in class_students["student_name"]:
        present = st.number_input(
            f"{student} Days Present",
            0, total_days,
            key=f"att_{student}_{selected_term}"
        )
        percent = round((present/total_days)*100,2)
        attendance_data.append({
            "student": student,
            "class_level": selected_class,
            "term": selected_term,
            "days_present": present,
            "total_days": total_days,
            "attendance_percent": percent
        })

    if st.button("Save Attendance"):
        attendance = attendance[
            ~((attendance["class_level"]==selected_class) &
              (attendance["term"]==selected_term))
        ]

        attendance = pd.concat([attendance,
                                pd.DataFrame(attendance_data)],
                               ignore_index=True)

        save(attendance, ATTENDANCE_FILE)
        st.success("Attendance saved")
        st.rerun()

# ==========================
# STUDENT
# ==========================
elif role == "student":
    st.header("Student Dashboard")

    student_name = user["username"]
    student_results = results[results["student"]==student_name]

    if student_results.empty:
        st.warning("No results yet")
        st.stop()

    selected_term = st.selectbox("Term", student_results["term"].unique())
    term_data = student_results[student_results["term"]==selected_term].iloc[0]

    st.metric("Average", term_data["average"])
    st.metric("Grade", term_data["grade"])
    st.metric("Rank", int(term_data["rank"]))

    # AI Prediction
    if len(student_results) >= 2:
        history = student_results.copy()
        history["term_order"] = history["term"].map(TERM_ORDER)
        history = history.sort_values("term_order")

        X = np.arange(len(history)).reshape(-1,1)
        y = history["average"].values

        model = LinearRegression()
        model.fit(X,y)

        prediction = model.predict([[len(history)]])[0]
        prediction = max(0,min(100,prediction))

        st.subheader("AI Prediction")
        st.info(f"Predicted Average: {round(prediction,2)}")
        st.info(f"Predicted Grade: {grade(prediction)}")

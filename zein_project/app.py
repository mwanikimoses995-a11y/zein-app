import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

st.set_page_config(page_title="Advanced School ERP AI", layout="wide")

# ==========================
# FILES AND DATA
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
ALL_SUBJECTS = COMPULSORY + GROUP_HUMANITIES + GROUP_TECH + ["IRE", "HRE", "Business", "Agriculture", "Computer", "French", "German", "Arabic", "Wood Technology", "Metal Work", "Building Construction", "Electricity"]

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

def load_data():
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
# CREATE FILES IF NOT EXIST
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"], [["admin", hash_password("1234"), "admin", ""]])
create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

users, students, marks, results, attendance = load_data()

# ==========================
# LOGIN & FORGOT PASSWORD
# ==========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    st.write("---")
    tab_login, tab_forget = st.tabs(["Login", "Forgot Password"])

    with tab_login:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            match = users[(users["username"]==username) & (users["password"]==hash_password(password))]
            if not match.empty:
                st.session_state.user = match.iloc[0].to_dict()
                st.experimental_rerun()
            else:
                st.error("Invalid username or password")

    with tab_forget:
        username_fp = st.text_input("Enter your username")
        question = st.text_input("Security Question: Who is Zein?")
        if st.button("Reset Password"):
            if username_fp not in users["username"].values:
                st.error("Username not found")
            elif question.strip().lower() != "zeiniszein":
                st.error("Incorrect answer")
            else:
                new_pass = st.text_input("Enter new password", type="password", key="new_pass")
                if new_pass and st.button("Save New Password", key="save_new_pass"):
                    users.loc[users["username"]==username_fp, "password"] = hash_password(new_pass)
                    save(users, USERS_FILE)
                    st.success("Password reset successfully")
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
if role=="student":
    st.header("📊 Student AI Dashboard")
    student_name = user["username"]
    users, students, marks, results, attendance = load_data()
    student_results = results[results["student"]==student_name]
    student_marks = marks[marks["student"]==student_name]
    student_attendance = attendance[attendance["student"]==student_name]

    if student_results.empty:
        st.warning("No results yet")
        st.stop()

    # Overall Performance Trend
    st.subheader("📈 Overall Performance Trend")
    history = student_results.copy()
    history["term_order"] = history["term"].map(TERM_ORDER)
    history = history.sort_values("term_order")
    fig, ax = plt.subplots()
    ax.bar(history["term"], history["average"], color='skyblue')
    ax.set_ylabel("Average Score"); ax.set_xlabel("Term"); ax.set_title("Average Score Over Terms")
    st.pyplot(fig)

    # Latest Subject-wise Marks
    latest_term = history.iloc[-1]["term"]
    latest_marks = student_marks[student_marks["term"]==latest_term]
    if not latest_marks.empty:
        st.subheader(f"📊 Marks by Subject ({latest_term})")
        fig2, ax2 = plt.subplots(figsize=(10,5))
        ax2.bar(latest_marks["subject"], latest_marks["marks"], color='orange')
        ax2.set_ylabel("Marks"); ax2.set_xlabel("Subject"); ax2.set_title(f"Subject-wise Marks for {latest_term}")
        ax2.set_ylim(0,100)
        plt.xticks(rotation=45, ha='right')
        st.pyplot(fig2)

        mean_mark = latest_marks["marks"].mean()
        st.metric("Mean Mark", round(mean_mark,2))
        st.metric("Overall Grade", grade(mean_mark))

    # AI Predictions for Next Term
    st.subheader("🔮 Zein AI Predictions for Next Term")
    predicted_marks = []
    subjects = student_marks["subject"].unique()
    for subj in subjects:
        subj_data = student_marks[student_marks["subject"]==subj].copy()
        subj_data["term_order"] = subj_data["term"].map(TERM_ORDER)
        subj_data = subj_data.sort_values("term_order")
        if len(subj_data) < 2:
            pred = subj_data["marks"].iloc[-1] if not subj_data.empty else 0
        else:
            X = np.arange(len(subj_data)).reshape(-1,1)
            y = subj_data["marks"].values
            model = LinearRegression()
            model.fit(X,y)
            pred = model.predict([[len(subj_data)]])[0]
        pred = max(0,min(100,pred))
        predicted_marks.append({"subject": subj, "predicted_marks": round(pred,2)})

    pred_df = pd.DataFrame(predicted_marks)
    st.dataframe(pred_df)

    expected_mean = pred_df["predicted_marks"].mean() if not pred_df.empty else 0
    st.metric("Expected Mean Mark", round(expected_mean,2))
    st.metric("Expected Grade", grade(expected_mean))

    # Subject Trends Across Terms
    if len(history) > 1:
        st.subheader("📊 Subject Trends Across Terms")
        fig3, ax3 = plt.subplots(figsize=(12,6))
        for subj in subjects:
            subj_data = student_marks[student_marks["subject"]==subj].copy()
            subj_data["term_order"] = subj_data["term"].map(TERM_ORDER)
            subj_data = subj_data.sort_values("term_order")
            ax3.plot(subj_data["term"], subj_data["marks"], marker='o', label=subj)
        ax3.set_ylabel("Marks"); ax3.set_xlabel("Term"); ax3.set_title("Subject Performance Trends")
        ax3.set_ylim(0,100)
        plt.xticks(rotation=45)
        ax3.legend(bbox_to_anchor=(1.05,1),loc='upper left')
        st.pyplot(fig3)

    # Attendance
    st.subheader("📋 Attendance")
    if not student_attendance.empty:
        st.dataframe(student_attendance[["term","attendance_percent"]])

# ==========================
# TEACHER / ADMIN DASHBOARD
# ==========================
elif role in ["teacher","admin"]:
    st.header(f"👩‍🏫 {role.capitalize()} Dashboard")
    users, students, marks, results, attendance = load_data()

    # --------------------------
    # ADMIN FEATURES
    # --------------------------
    if role=="admin":
        st.subheader("➕ Add Users")
        user_type = st.selectbox("User Type", ["Student","Teacher"])
        if user_type=="Student":
            student_name = st.text_input("Student Full Name")
            class_level = st.selectbox("Class Level", CLASSES)
            if st.button("Add Student"):
                if student_name and class_level:
                    if student_name in students["student_name"].values:
                        st.warning("Student already exists")
                    else:
                        students = pd.concat([students,pd.DataFrame([{"student_name":student_name,"class_level":class_level}])], ignore_index=True)
                        users = pd.concat([users,pd.DataFrame([{"username":student_name,"password":hash_password("1234"),"role":"student","subject":""}])], ignore_index=True)
                        save(students, STUDENTS_FILE)
                        save(users, USERS_FILE)
                        st.success(f"Student {student_name} added successfully")

        if user_type=="Teacher":
            subject = st.text_input("Subject")
            number = st.text_input("Number / ID")
            if st.button("Add Teacher"):
                if subject and number:
                    username = f"{subject}{number}"
                    if username in users["username"].values:
                        st.warning("Teacher already exists")
                    else:
                        users = pd.concat([users,pd.DataFrame([{"username":username,"password":hash_password("1234"),"role":"teacher","subject":subject}])], ignore_index=True)
                        save(users, USERS_FILE)
                        st.success(f"Teacher {username} added successfully")

        st.subheader("🗂️ All Users")
        st.dataframe(users)

        st.subheader("❌ Remove User")
        remove_user = st.selectbox("Select User to Remove", users["username"].values)
        if st.button("Remove User"):
            users = users[users["username"]!=remove_user]
            students = students[students["student_name"]!=remove_user]
            marks = marks[marks["student"]!=remove_user]
            results = results[results["student"]!=remove_user]
            save(users, USERS_FILE)
            save(students, STUDENTS_FILE)
            save(marks, MARKS_FILE)
            save(results, RESULTS_FILE)
            st.success(f"User {remove_user} removed successfully")

        st.subheader("📚 Students by Class")
        for cls in CLASSES:
            st.write(f"**{cls}**")
            class_students = students[students["class_level"]==cls]
            st.write(class_students["student_name"].values if not class_students.empty else "No students")

    # --------------------------
    # TEACHER: ENTER MARKS
    # --------------------------
    if role=="teacher":
        selected_class = st.selectbox("Select Class", CLASSES)
        class_students = students[students["class_level"]==selected_class]
        if class_students.empty:
            st.warning("No students in this class")
            st.stop()
        st.subheader("✏️ Enter Marks for Students")
        selected_student = st.selectbox("Select Student", class_students["student_name"].values)
        term = st.selectbox("Select Term", TERMS)
        comp_marks = {}
        st.markdown("**Compulsory Subjects**")
        for subj in COMPULSORY[:-1]:
            comp_marks[subj] = st.number_input(f"{subj} Marks", min_value=0, max_value=100, value=0, key=f"{selected_student}_{subj}")
        # Humanities
        humanity_subject = st.selectbox("Select One Humanity", GROUP_HUMANITIES)
        humanity_mark = st.number_input(f"{humanity_subject} Marks", min_value=0, max_value=100, value=0)
        # Technical
        technical_subject = st.selectbox("Select One Technical", GROUP_TECH)
        technical_mark = st.number_input(f"{technical_subject} Marks", min_value=0, max_value=100, value=0)

        if st.button("Save Marks"):
            new_entries=[]
            for subj, mark in comp_marks.items():
                marks = marks[~((marks["student"]==selected_student) & (marks["term"]==term) & (marks["subject"]==subj))]
                new_entries.append({"student":selected_student,"class_level":selected_class,"term":term,"subject":subj,"marks":mark})
            # Humanities
            marks = marks[~((marks["student"]==selected_student) & (marks["term"]==term) & (marks["subject"]==humanity_subject))]
            new_entries.append({"student":selected_student,"class_level":selected_class,"term":term,"subject":humanity_subject,"marks":humanity_mark})
            # Technical
            marks = marks[~((marks["student"]==selected_student) & (marks["term"]==term) & (marks["subject"]==technical_subject))]
            new_entries.append({"student":selected_student,"class_level":selected_class,"term":term,"subject":technical_subject,"marks":technical_mark})
            marks = pd.concat([marks,pd.DataFrame(new_entries)], ignore_index=True)
            save(marks, MARKS_FILE)
            st.success(f"Marks saved for {selected_student} for {term}")

    # --------------------------
    # CLASS MARKS & PREDICTIONS
    # --------------------------
    st.subheader("📊 Student Marks & AI Predictions")
    table_data=[]
    selected_class_analysis = st.selectbox("Select Class for Analysis", CLASSES, key="analysis_class")
    class_students = students[students["class_level"]==selected_class_analysis]
    for student in class_students["student_name"].values:
        student_marks = marks[marks["student"]==student]
        latest_term_marks = student_marks[student_marks["term"]==TERMS[-1]]
        mean_mark = latest_term_marks["marks"].mean() if not latest_term_marks.empty else 0

        student_prediction=[]
        subjects = student_marks["subject"].unique()
        for subj in subjects:
            subj_data = student_marks[student_marks["subject"]==subj].copy()
            subj_data["term_order"] = subj_data["term"].map(TERM_ORDER)
            subj_data = subj_data.sort_values("term_order")
            if len(subj_data)<2:
                pred=subj_data["marks"].iloc[-1] if not subj_data.empty else 0
            else:
                X=np.arange(len(subj_data)).reshape(-1,1)
                y=subj_data["marks"].values
                model=LinearRegression()
                model.fit(X,y)
                pred=model.predict([[len(subj_data)]])[0]
            pred=max(0,min(100,pred))
            student_prediction.append(pred)
        expected_mean = np.mean(student_prediction) if student_prediction else mean_mark
        table_data.append({"Student":student,"Latest Mean":round(mean_mark,2),"Expected Mean":round(expected_mean,2),"Expected Grade":grade(expected_mean)})

    class_df=pd.DataFrame(table_data)
    st.dataframe(class_df)

    fig, ax = plt.subplots(figsize=(10,5))
    ax.bar(class_df["Student"], class_df["Expected Mean"], color='green')
    ax.set_ylabel("Expected Mean"); ax.set_xlabel("Student"); ax.set_title(f"Class {selected_class_analysis} Predictions")
    ax.set_ylim(0,100)
    plt.xticks(rotation=45)
    st.pyplot(fig)

    overall_expected_mean = class_df["Expected Mean"].mean() if not class_df.empty else 0
    st.subheader("🔮 Summary Predictions")
    st.metric("Class Expected Mean Mark", round(overall_expected_mean,2))
    st.metric("Class Expected Grade", grade(overall_expected_mean))

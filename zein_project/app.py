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
GROUP_1 = ["Physics", "CRE", "IRE", "HRE"]
GROUP_2 = ["History", "Geography"]
GROUP_3 = ["Business", "Agriculture", "Computer", "French", "German", "Arabic"]
GROUP_4 = ["Wood Technology", "Metal Work", "Building Construction", "Electricity"]
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
# CREATE FILES IF NOT EXIST
# ==========================
create_file(USERS_FILE, ["username","password","role","subject"], [["admin", hash_password("1234"), "admin", ""]])
create_file(STUDENTS_FILE, ["student_name","class_level"])
create_file(MARKS_FILE, ["student","class_level","term","subject","marks"])
create_file(RESULTS_FILE, ["student","class_level","term","total","average","grade","rank"])
create_file(ATTENDANCE_FILE, ["student","class_level","term","days_present","total_days","attendance_percent"])

users, students, marks, results, attendance = load()

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
# ADMIN DASHBOARD
# ==========================
if role=="admin":
    st.header("🛠 Admin Dashboard")
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["Add Student","Add Teacher","Add Admin","View Users","Manage Users"])

    # ---- Add Student ----
    with tab1:
        st.subheader("➕ Add Student")
        name = st.text_input("Student Name", key="student_add")
        cls = st.selectbox("Class Level", CLASSES, key="student_class_add")
        if st.button("Add Student"):
            if not name: st.error("Enter name")
            elif name in students["student_name"].values: st.error("Student exists")
            else:
                new_student = pd.DataFrame([{"student_name": name, "class_level": cls}])
                students = pd.concat([students, new_student], ignore_index=True)
                save(students, STUDENTS_FILE)
                new_user = pd.DataFrame([{"username": name, "password": hash_password("1234"), "role":"student","subject":""}])
                users = pd.concat([users,new_user],ignore_index=True)
                save(users,USERS_FILE)
                st.success(f"Student {name} added with password 1234")
                st.experimental_rerun()

    # ---- Add Teacher ----
    with tab2:
        st.subheader("➕ Add Teacher")
        subject = st.selectbox("Subject", ALL_SUBJECTS, key="teacher_subject")
        number = st.number_input("Teacher Number",1,50,1, key="teacher_number")
        username = f"{subject.lower()}{number}"
        st.info(f"Username: {username}")
        if st.button("Add Teacher"):
            if username in users["username"].values: st.error("Teacher exists")
            else:
                new_user = pd.DataFrame([{"username": username,"password":hash_password("1234"),
                                          "role":"teacher","subject":subject}])
                users = pd.concat([users,new_user],ignore_index=True)
                save(users,USERS_FILE)
                st.success(f"Teacher {username} added with password 1234")
                st.experimental_rerun()

    # ---- Add Admin ----
    with tab3:
        st.subheader("➕ Add Admin")
        new_admin = st.text_input("New Admin Username")
        if st.button("Add Admin"):
            if not new_admin: st.error("Enter username")
            elif new_admin in users["username"].values: st.error("Username exists")
            else:
                new_user = pd.DataFrame([{"username": new_admin,"password":hash_password("1234"),
                                          "role":"admin","subject":""}])
                users = pd.concat([users,new_user],ignore_index=True)
                save(users,USERS_FILE)
                st.success(f"Admin {new_admin} added with password 1234")
                st.experimental_rerun()

    # ---- View Users ----
    with tab4:
        st.subheader("👥 All Users")
        if not users.empty:
            display = users[["username","role","subject"]].copy()
            display["Password"] = "1234"
            st.dataframe(display,use_container_width=True)
            st.subheader("📊 User Stats")
            col1,col2,col3 = st.columns(3)
            col1.metric("Total Users", len(users))
            col2.metric("Teachers", len(users[users["role"]=="teacher"]))
            col3.metric("Students", len(users[users["role"]=="student"]))

    # ---- Manage Users ----
    with tab5:
        st.subheader("🗑 Remove User (Default admin protected)")
        remove_user = st.selectbox("Select User", users["username"].values)
        if st.button("Remove User"):
            if remove_user=="admin":
                st.error("Default admin cannot be removed!")
            else:
                users = users[users["username"]!=remove_user]
                save(users,USERS_FILE)
                st.success(f"User {remove_user} removed")
                st.experimental_rerun()

# ==========================
# TEACHER DASHBOARD
# ==========================
elif role=="teacher":
    st.header("👩‍🏫 Teacher Dashboard")
    selected_class = st.selectbox("Select Class", CLASSES)
    selected_term = st.selectbox("Select Term", TERMS)
    class_students = students[students["class_level"]==selected_class]
    if class_students.empty: st.warning("No students"); st.stop()
    selected_student = st.selectbox("Select Student", class_students["student_name"].values)
    tab1, tab2 = st.tabs(["Marks Entry","Attendance"])

    # Marks Entry
    with tab1:
        st.subheader(f"Enter Marks for {selected_student}")
        student_data = []
        st.write("**Compulsory Subjects:**")
        for subject in COMPULSORY:
            m = st.number_input(subject,0,100,0,key=f"m_{subject}")
            student_data.append((subject,m))
        st.write("**Group 1:**")
        g1 = st.radio("Group1",GROUP_1,key="g1_radio")
        student_data.append((g1,st.number_input(f"{g1} marks",0,100,0,key="g1_marks")))
        st.write("**Group 2:**")
        g2 = st.radio("Group2",GROUP_2,key="g2_radio")
        student_data.append((g2,st.number_input(f"{g2} marks",0,100,0,key="g2_marks")))
        st.write("**Group 3:**")
        g3 = st.radio("Group3",GROUP_3,key="g3_radio")
        student_data.append((g3,st.number_input(f"{g3} marks",0,100,0,key="g3_marks")))
        if st.button("Save Marks"):
            _, _, marks_fresh, results_fresh, _ = load()
            marks_filtered = marks_fresh[~((marks_fresh["student"]==selected_student)&
                                           (marks_fresh["term"]==selected_term)&
                                           (marks_fresh["class_level"]==selected_class))]
            df = pd.DataFrame(student_data,columns=["subject","marks"])
            df.insert(0,"term",selected_term)
            df.insert(0,"class_level",selected_class)
            df.insert(0,"student",selected_student)
            marks_updated = pd.concat([marks_filtered,df],ignore_index=True)
            save(marks_updated,MARKS_FILE)

            # Update results
            total = df["marks"].sum()
            avg = df["marks"].mean()
            results_filtered = results_fresh[~((results_fresh["student"]==selected_student)&
                                               (results_fresh["term"]==selected_term)&
                                               (results_fresh["class_level"]==selected_class))]
            results_updated = pd.concat([results_filtered,pd.DataFrame([{"student":selected_student,
                                                                         "class_level":selected_class,
                                                                         "term":selected_term,
                                                                         "total":total,
                                                                         "average":round(avg,2),
                                                                         "grade":grade(avg),
                                                                         "rank":0}])],ignore_index=True)
            term_results = results_updated[(results_updated["class_level"]==selected_class)&
                                           (results_updated["term"]==selected_term)].copy()
            term_results = term_results.sort_values("average",ascending=False).reset_index(drop=True)
            term_results["rank"] = range(1,len(term_results)+1)
            results_final = results_updated[~((results_updated["class_level"]==selected_class)&
                                             (results_updated["term"]==selected_term))].reset_index(drop=True)
            results_final = pd.concat([results_final,term_results],ignore_index=True)
            save(results_final,RESULTS_FILE)
            st.success(f"Marks saved! Avg: {round(avg,2)}, Grade: {grade(avg)}")

    # Attendance
    with tab2:
        st.subheader(f"Mark Attendance for {selected_student}")
        total_days = st.number_input("Total Days in Term",1,365,100)
        present = st.number_input("Days Present",0,total_days,0)
        if st.button("Save Attendance"):
            _, _, _, _, attendance_fresh = load()
            percent = round((present/total_days)*100,2)
            attendance_filtered = attendance_fresh[~((attendance_fresh["student"]==selected_student)&
                                                    (attendance_fresh["term"]==selected_term)&
                                                    (attendance_fresh["class_level"]==selected_class))]
            attendance_updated = pd.concat([attendance_filtered,
                                           pd.DataFrame([{"student":selected_student,
                                                          "class_level":selected_class,
                                                          "term":selected_term,
                                                          "days_present":present,
                                                          "total_days":total_days,
                                                          "attendance_percent":percent}])],
                                           ignore_index=True)
            save(attendance_updated,ATTENDANCE_FILE)
            st.success(f"Attendance saved: {percent}%")

# ==========================
# STUDENT DASHBOARD
# ==========================
elif role=="student":
    st.header("📊 Student AI Dashboard")
    student_name = user["username"]
    users, students, marks, results, attendance = load()
    student_results = results[results["student"]==student_name]
    student_marks = marks[marks["student"]==student_name]
    student_attendance = attendance[attendance["student"]==student_name]
    if student_results.empty: st.warning("No results yet"); st.stop()

    # Overall Trend
    st.subheader("📈 Overall Performance Trend")
    history = student_results.copy()
    history["term_order"] = history["term"].map(TERM_ORDER)
    history = history.sort_values("term_order")
    fig, ax = plt.subplots()
    ax.bar(history["term"], history["average"], color='skyblue')
    ax.set_ylabel("Average Score"); ax.set_xlabel("Term"); ax.set_title("Average Score Over Terms")
    st.pyplot(fig)

    # Next Term Prediction
    pred_next = None
    future_mean = None
    if len(history)>=2:
        X = np.arange(len(history)).reshape(-1,1)
        y = history["average"].values
        model = LinearRegression()
        model.fit(X,y)
        pred_next = model.predict([[len(history)]])[0]
        pred_next = max(0,min(100,pred_next))
        future_mean = np.append(y,pred_next).mean()
        st.subheader("🔮 Next Term Prediction")
        col1,col2,col3 = st.columns(3)
        col1.metric("Predicted Average", round(pred_next,2))
        col2.metric("Predicted Grade", grade(pred_next))
        col3.metric("Predicted Future Mean", round(future_mean,2))

    # Latest term subject chart
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
        weakest = latest_marks.sort_values("marks").iloc[0]
        strongest = latest_marks.sort_values("marks",ascending=False).iloc[0]
        st.error(f"Weakest Subject: {weakest['subject']} ({weakest['marks']}%)")
        st.success(f"Strongest Subject: {strongest['subject']} ({strongest['marks']}%)")
        advice = ""
        if weakest["marks"]<50: advice += f"Focus on {weakest['subject']} daily. "
        elif weakest["marks"]<60: advice += f"Review {weakest['subject']} weekly. "
        if pred_next is not None:
            if pred_next>=75: advice += "Keep up the good work! "
            elif pred_next<60: advice += "Increase study and seek help."
        st.info(f"🤖 AI Advice: {advice}")

    # Subject trend across terms
    if len(history)>1:
        st.subheader("📊 Subject Trends Across Terms")
        subjects = student_marks["subject"].unique()
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

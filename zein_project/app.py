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
    try:
        users = pd.read_csv(USERS_FILE) if os.path.exists(USERS_FILE) else pd.DataFrame(columns=["username","password","role","subject"])
        students = pd.read_csv(STUDENTS_FILE) if os.path.exists(STUDENTS_FILE) else pd.DataFrame(columns=["student_name","class_level"])
        marks = pd.read_csv(MARKS_FILE) if os.path.exists(MARKS_FILE) else pd.DataFrame(columns=["student","class_level","term","subject","marks"])
        results = pd.read_csv(RESULTS_FILE) if os.path.exists(RESULTS_FILE) else pd.DataFrame(columns=["student","class_level","term","total","average","grade","rank"])
        attendance = pd.read_csv(ATTENDANCE_FILE) if os.path.exists(ATTENDANCE_FILE) else pd.DataFrame(columns=["student","class_level","term","days_present","total_days","attendance_percent"])
        return users, students, marks, results, attendance
    except Exception as e:
        st.error(f"Error loading files: {e}")
        st.stop()

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
            [["admin", hash_password("1234"), "admin", ""]])

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

    # Create tabs for different admin functions
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["Add Student", "Add Teacher", "View Users"])

    # ----- ADD STUDENT TAB -----
    with admin_tab1:
        st.subheader("➕ Add Student")
        student_name = st.text_input("Student Name", key="student_name_input").strip()
        student_class = st.selectbox("Class Level", CLASSES, key="student_class_select")

        if st.button("Add Student", key="add_student_btn"):
            if not student_name:
                st.error("❌ Student name cannot be empty")
            elif student_name in students.student_name.values:
                st.error("❌ Student already exists")
            else:
                # Add student record
                new_student = pd.DataFrame([{
                    "student_name": student_name,
                    "class_level": student_class
                }])
                students = pd.concat([students, new_student], ignore_index=True)
                save(students, STUDENTS_FILE)

                # Add student user account
                new_user = pd.DataFrame([{
                    "username": student_name,
                    "password": hash_password("1234"),
                    "role": "student",
                    "subject": ""
                }])
                users = pd.concat([users, new_user], ignore_index=True)
                save(users, USERS_FILE)

                st.success(f"✅ Student '{student_name}' added successfully! Password: 1234")
                st.rerun()

    # ----- ADD TEACHER TAB -----
    with admin_tab2:
        st.subheader("➕ Add Teacher")
        teacher_subject = st.selectbox("Subject", ALL_SUBJECTS, key="teacher_subject_select")
        teacher_number = st.number_input("Teacher Number", min_value=1, max_value=10, value=1, key="teacher_number_input")
        teacher_username = f"{teacher_subject.lower()}{teacher_number}"

        st.info(f"📝 Username will be: **{teacher_username}**")

        if st.button("Add Teacher", key="add_teacher_btn"):
            if teacher_username in users.username.values:
                st.error(f"❌ Teacher username '{teacher_username}' already exists")
            else:
                new_user = pd.DataFrame([{
                    "username": teacher_username,
                    "password": hash_password("1234"),
                    "role": "teacher",
                    "subject": teacher_subject
                }])
                users = pd.concat([users, new_user], ignore_index=True)
                save(users, USERS_FILE)

                st.success(f"✅ Teacher '{teacher_username}' ({teacher_subject}) added successfully! Password: 1234")
                st.rerun()

    # ----- VIEW USERS TAB -----
    with admin_tab3:
        st.subheader("👥 All Users")
        
        if not users.empty:
            display_users = users[["username", "role", "subject"]].copy()
            display_users["Password"] = "1234"
            st.dataframe(display_users, use_container_width=True)
            
            st.subheader("📊 User Statistics")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Users", len(users))
            col2.metric("Teachers", len(users[users.role=="teacher"]))
            col3.metric("Students", len(users[users.role=="student"]))
        else:
            st.info("No users found")

# =====================================================
# TEACHER DASHBOARD
# =====================================================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    if students.empty:
        st.warning("⚠️ No students found in the system")
        st.stop()

    selected_class = st.selectbox("Select Class", CLASSES)
    selected_term = st.selectbox("Select Term", TERMS)

    class_students = students[students.class_level==selected_class]

    if class_students.empty:
        st.warning(f"⚠️ No students in {selected_class}")
        st.stop()

    selected_student = st.selectbox("Select Student", class_students.student_name.values)

    tab1, tab2 = st.tabs(["Marks Entry","Attendance"])

    # ================= MARKS =================
    with tab1:
        st.subheader(f"📝 Enter Marks for {selected_student}")

        student_data = []

        st.write("**Compulsory Subjects:**")
        for subject in COMPULSORY:
            m = st.number_input(f"{subject}", 0, 100, value=0, key=f"mark_{subject}")
            student_data.append((subject, m))

        st.write("**Group 1 (Select One):**)\n        g1 = st.radio("Group 1", GROUP_1, key="group1_radio")
        g1_marks = st.number_input(f"{g1} Marks", 0, 100, value=0, key="group1_marks")
        student_data.append((g1, g1_marks))

        st.write("**Group 2 (Select One):**)\n        g2 = st.radio("Group 2", GROUP_2, key="group2_radio")
        g2_marks = st.number_input(f"{g2} Marks", 0, 100, value=0, key="group2_marks")
        student_data.append((g2, g2_marks))

        st.write("**Group 3 (Select One):**)\n        g3 = st.radio("Group 3", GROUP_3, key="group3_radio")
        g3_marks = st.number_input(f"{g3} Marks", 0, 100, value=0, key="group3_marks")
        student_data.append((g3, g3_marks))

        if st.button("Save Marks", key="save_marks_btn"):
            try:
                users_fresh, students_fresh, marks_fresh, results_fresh, attendance_fresh = load()
                
                marks_filtered = marks_fresh[~((marks_fresh.student==selected_student) & (marks_fresh.term==selected_term) & (marks_fresh.class_level==selected_class))].reset_index(drop=True)

                df = pd.DataFrame(student_data, columns=["subject","marks"])
                df.insert(0, "term", selected_term)
                df.insert(0, "class_level", selected_class)
                df.insert(0, "student", selected_student)

                marks_updated = pd.concat([marks_filtered, df], ignore_index=True)
                save(marks_updated, MARKS_FILE)

                total = df.marks.sum()
                avg = df.marks.mean()

                results_filtered = results_fresh[~((results_fresh.student==selected_student) & (results_fresh.term==selected_term) & (results_fresh.class_level==selected_class))].reset_index(drop=True)

                results_updated = pd.concat([results_filtered, pd.DataFrame([{
                    "student": selected_student,
                    "class_level": selected_class,
                    "term": selected_term,
                    "total": total,
                    "average": round(avg, 2),
                    "grade": grade(avg),
                    "rank": 0
                }])], ignore_index=True)

                term_results = results_updated[(results_updated.class_level==selected_class) & (results_updated.term==selected_term)].copy()
                term_results = term_results.sort_values("average", ascending=False).reset_index(drop=True)
                term_results["rank"] = range(1, len(term_results)+1)

                results_final = results_updated[~((results_updated.class_level==selected_class) & (results_updated.term==selected_term))].reset_index(drop=True)
                results_final = pd.concat([results_final, term_results], ignore_index=True)
                
                save(results_final, RESULTS_FILE)

                st.success(f"✅ Marks saved for {selected_student}! Average: {round(avg, 2)}, Grade: {grade(avg)}")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving marks: {str(e)}")

    # ================= ATTENDANCE =================
    with tab2:
        st.subheader(f"📋 Mark Attendance for {selected_student}")

        total_days = st.number_input("Total Days in Term", min_value=1, max_value=365, value=100, key="total_days")
        present = st.number_input("Days Present", min_value=0, max_value=total_days, value=0, key="days_present")

        if st.button("Save Attendance", key="save_attendance_btn"):
            try:
                users_fresh, students_fresh, marks_fresh, results_fresh, attendance_fresh = load()
                
                percent = round((present/total_days)*100, 2)

                attendance_filtered = attendance_fresh[~((attendance_fresh.student==selected_student) & (attendance_fresh.term==selected_term) & (attendance_fresh.class_level==selected_class))].reset_index(drop=True)

                attendance_updated = pd.concat([attendance_filtered, pd.DataFrame([{
                    "student": selected_student,
                    "class_level": selected_class,
                    "term": selected_term,
                    "days_present": present,
                    "total_days": total_days,
                    "attendance_percent": percent
                }])], ignore_index=True)

                save(attendance_updated, ATTENDANCE_FILE)
                st.success(f"✅ Attendance saved! Percentage: {percent}%")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error saving attendance: {str(e)}")

# =====================================================
# STUDENT DASHBOARD
# =====================================================
elif role == "student":

    st.header("📊 Student Dashboard")

    student_name = user["username"]

    student_results = results[results.student==student_name] if not results.empty else pd.DataFrame()
    student_marks = marks[marks.student==student_name] if not marks.empty else pd.DataFrame()
    student_attendance = attendance[attendance.student==student_name] if not attendance.empty else pd.DataFrame()

    if student_results.empty:
        st.warning("⚠️ No results yet. Marks will appear here once teachers enter them.")
        st.stop()

    selected_term = st.selectbox("Select Term", student_results.term.unique())

    term_data = student_results[student_results.term==selected_term]

    if not term_data.empty:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📈 Average", term_data.iloc[0]["average"])
        
        with col2:
            st.metric("🎯 Grade", term_data.iloc[0]["grade"])
        
        with col3:
            st.metric("🏆 Rank in Class", int(term_data.iloc[0]["rank"]))

        st.subheader("📝 Your Marks")
        term_marks = student_marks[student_marks.term==selected_term]
        if not term_marks.empty:
            marks_display = term_marks[["subject", "marks"]].copy()
            st.dataframe(marks_display, use_container_width=True)
        
        st.subheader("📋 Your Attendance")
        term_attendance = student_attendance[student_attendance.term==selected_term]
        if not term_attendance.empty:
            attendance_display = term_attendance[["days_present", "total_days", "attendance_percent"]].copy()
            attendance_display.columns = ["Days Present", "Total Days", "Attendance %"]
            st.dataframe(attendance_display, use_container_width=True)

        if len(student_results) >= 2:

            st.subheader("🤖 Performance Prediction")
            
            history = student_results.sort_values("term").reset_index(drop=True)
            X = np.arange(len(history)).reshape(-1, 1)
            y = history.average.values

            model = LinearRegression()
            model.fit(X, y)

            future_index = [[len(history)]]
            prediction = model.predict(future_index)[0]
            
            prediction = max(0, min(100, prediction))

            col1, col2 = st.columns(2)
            with col1:
                st.info(f"📊 Predicted Next Term Average: **{round(prediction, 2)}**")
            with col2:
                st.info(f"🎯 Predicted Grade: **{grade(prediction)}**")
    else:
        st.error("❌ No data available for the selected term")

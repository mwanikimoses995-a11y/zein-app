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
COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
GROUP_1 = ["CRE", "Physics"]
GROUP_2 = ["History", "Geography"]
GROUP_3 = ["Business", "Agriculture", "French", "HomeScience", "Computer"]
ALL_SUBJECTS = COMPULSORY + GROUP_1 + GROUP_2 + GROUP_3

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

create_file(USERS_FILE, ["username", "password", "role", "subject"], [["admin", hash_password("12345"), "admin", ""]])
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
# LOGIN / FORGOT PASSWORD
# =====================================================
if "user" not in st.session_state:

    st.title("🎓 School Portal Login")

    forgot_pw = st.checkbox("Forgot Password?")

    if forgot_pw:
        username = st.text_input("Enter Username", key="fp_username")
        sec_answer = st.text_input("Security Question: Who is Zein?", key="fp_answer")

        # Show new password fields immediately
        new_password = st.text_input("Enter New Password", type="password", key="fp_new")
        confirm_password = st.text_input("Confirm New Password", type="password", key="fp_confirm")

        if st.button("Reset Password", key="fp_reset"):
            user_match = users[users.username == username]
            if user_match.empty:
                st.error("Username not found")
            elif sec_answer.strip().lower() != "zeiniszein":
                st.error("Incorrect answer to security question")
            elif new_password != confirm_password:
                st.error("Passwords do not match")
            elif new_password.strip() == "":
                st.error("Password cannot be empty")
            else:
                users.loc[users.username == username, "password"] = hash_password(new_password)
                save(users, USERS_FILE)
                st.success("Password reset successfully! You can now login.")
        st.stop()

    else:
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

user = st.session_state.user
role = user["role"]

st.sidebar.success(f"Logged in as {user['username']} ({role})")
if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

# Reload data after login/logout
users, students, marks, attendance, results = load_all()

# =====================================================
# TEACHER PANEL
# =====================================================
if role == "teacher":
    st.header("👩‍🏫 Teacher Dashboard")

    if students.empty:
        st.warning("No students available.")
    else:

        tab1, tab2 = st.tabs(["Manual Entry", "Upload CSV"])

        # ======== TAB 1: Manual Entry ========
        with tab1:

            selected_student = st.selectbox("Select Student", students["student_name"], key="manual_student_select")
            st.divider()
            st.subheader("Enter Student Subjects & Marks")
            student_data = []

            # COMPULSORY SUBJECTS
            st.markdown("### 📘 Compulsory Subjects (All Required)")
            for subject in COMPULSORY:
                mark = st.number_input(f"{subject} Marks", min_value=0, max_value=100, key=f"{selected_student}_{subject}")
                student_data.append((subject, mark))

            # GROUP 1
            st.markdown("### 🔬 Choose ONE: CRE or Physics")
            group1_choice = st.radio("Group 1", GROUP_1, key=f"group1_{selected_student}")
            mark1 = st.number_input(f"{group1_choice} Marks", min_value=0, max_value=100, key=f"{selected_student}_{group1_choice}")
            student_data.append((group1_choice, mark1))

            # GROUP 2
            st.markdown("### 🌍 Choose ONE: History or Geography")
            group2_choice = st.radio("Group 2", GROUP_2, key=f"group2_{selected_student}")
            mark2 = st.number_input(f"{group2_choice} Marks", min_value=0, max_value=100, key=f"{selected_student}_{group2_choice}")
            student_data.append((group2_choice, mark2))

            # GROUP 3
            st.markdown("### 💼 Choose ONE Technical Subject")
            group3_choice = st.radio("Group 3", GROUP_3, key=f"group3_{selected_student}")
            mark3 = st.number_input(f"{group3_choice} Marks", min_value=0, max_value=100, key=f"{selected_student}_{group3_choice}")
            student_data.append((group3_choice, mark3))

            if st.button("Save Student Marks (Manual Entry)"):
                # Remove existing marks for this student
                marks = marks[marks.student != selected_student].copy()

                # Append new marks
                new_marks_df = pd.DataFrame(student_data, columns=["subject", "marks"])
                new_marks_df.insert(0, "student", selected_student)
                marks = pd.concat([marks, new_marks_df], ignore_index=True)
                save(marks, MARKS_FILE)

                # Update results
                student_marks = marks[marks.student == selected_student]
                total = float(student_marks.marks.sum())
                average = float(student_marks.marks.mean())
                grade = calculate_grade(average)

                results = results[results.student != selected_student].copy()
                new_result_df = pd.DataFrame(
                    [{"student": selected_student, "total_marks": total, "average": round(average,2), "grade": grade}]
                )
                results = pd.concat([results, new_result_df], ignore_index=True)
                save(results, RESULTS_FILE)

                st.success("Marks saved successfully ✅")
                st.rerun()

        # ======== TAB 2: CSV Upload ========
        with tab2:
            st.subheader("📥 Step 1: Download CSV Template")
            template_rows = []
            for student in students["student_name"]:
                for subj in COMPULSORY + [GROUP_1[0], GROUP_2[0], GROUP_3[0]]:
                    template_rows.append([student, subj, 0])
            template_df = pd.DataFrame(template_rows, columns=["student","subject","marks"])
            st.download_button("Download CSV Template", data=template_df.to_csv(index=False), file_name="marks_template.csv", mime="text/csv")

            st.subheader("📤 Step 2: Upload Completed CSV")
            uploaded_file = st.file_uploader("Upload CSV (student, subject, marks)", type=["csv"])
            if uploaded_file:
                uploaded_df = pd.read_csv(uploaded_file)
                if not {"student","subject","marks"}.issubset(uploaded_df.columns):
                    st.error("CSV must contain student, subject, marks")
                else:
                    st.success("File uploaded ✅")
                    st.dataframe(uploaded_df)
                    if st.button("Save Uploaded Marks (CSV)"):
                        error_flag = False
                        for student in uploaded_df["student"].unique():
                            if student not in students["student_name"].values:
                                st.error(f"{student} not registered")
                                error_flag = True
                            s_df = uploaded_df[uploaded_df.student==student]
                            subjects = s_df.subject.tolist()
                            if len(subjects) > 8: error_flag=True
                            if len(set(subjects)&set(GROUP_1))>1: error_flag=True
                            if len(set(subjects)&set(GROUP_2))>1: error_flag=True
                            if len(set(subjects)&set(GROUP_3))>1: error_flag=True
                        if not error_flag:
                            for _, row in uploaded_df.iterrows():
                                marks = marks[~((marks.student==row.student)&(marks.subject==row.subject))].copy()
                            marks = pd.concat([marks, uploaded_df], ignore_index=True)
                            save(marks, MARKS_FILE)

                            # Update results
                            for student in uploaded_df.student.unique():
                                student_marks = marks[marks.student == student]
                                total = float(student_marks.marks.sum())
                                average = float(student_marks.marks.mean())
                                grade = calculate_grade(average)

                                results = results[results.student != student].copy()
                                new_result_df = pd.DataFrame(
                                    [{"student": student, "total_marks": total, "average": round(average,2), "grade": grade}]
                                )
                                results = pd.concat([results, new_result_df], ignore_index=True)
                            save(results, RESULTS_FILE)
                            st.success("All marks saved ✅")
                            st.rerun()

# =====================================================
# STUDENT PANEL
# =====================================================
elif role == "student":
    st.header(f"📊 Results for {user['username']}")
    student_name = user["username"]

    student_marks = marks[marks.student==student_name]
    student_result = results[results.student==student_name]

    if not student_marks.empty:
        st.subheader("Subject Marks")
        st.table(student_marks)
        if len(student_marks) > 1:
            st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty:
        st.metric("Total Marks", student_result.iloc[0]["total_marks"])
        st.metric("Average", student_result.iloc[0]["average"])
        st.metric("Grade", student_result.iloc[0]["grade"])

    if len(student_marks) > 1:
        X = np.arange(len(student_marks)).reshape(-1,1)
        y = student_marks.marks.values
        model = LinearRegression()
        model.fit(X,y)
        prediction = model.predict([[len(y)]])[0]
        st.info(f"📈 Predicted next mark: {round(prediction,1)}")

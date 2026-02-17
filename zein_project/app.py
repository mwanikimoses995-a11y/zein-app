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

user = st.session_state.user
role = user["role"]

st.sidebar.success(f"Logged in as {user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()

users, students, marks, attendance, results = load_all()

# =====================================================
# TEACHER PANEL
# =====================================================
if role == "teacher":

    st.header("👩‍🏫 Teacher Dashboard")

    st.subheader("📥 Step 1: Download Template")

    # Create template dataframe
    template_df = pd.DataFrame({
        "student": ["student_username"],
        "subject": ["English"],
        "marks": [75]
    })

    st.download_button(
        label="Download CSV Template",
        data=template_df.to_csv(index=False),
        file_name="marks_template.csv",
        mime="text/csv"
    )

    st.info("""
    📌 Instructions:
    1. Download the template.
    2. Fill in student usernames exactly as registered.
    3. Subject must match available subjects.
    4. Marks must be between 0 and 100.
    5. A student can have MAXIMUM 8 subjects only.
    6. Save the file as CSV.
    7. Upload below and click 'Save Uploaded Marks'.
    """)

    st.subheader("📤 Step 2: Upload Completed CSV")

    uploaded_file = st.file_uploader(
        "Upload CSV (student, subject, marks)",
        type=["csv"]
    )

    if uploaded_file is not None:

        try:
            uploaded_df = pd.read_csv(uploaded_file)

            required_columns = {"student", "subject", "marks"}

            if not required_columns.issubset(uploaded_df.columns):
                st.error("CSV must contain: student, subject, marks")
            else:
                st.success("File uploaded successfully ✅")
                st.dataframe(uploaded_df)

                if st.button("Save Uploaded Marks"):

                    error_flag = False

                    for student in uploaded_df["student"].unique():

                        existing_subjects = marks[marks.student == student]["subject"].nunique()
                        new_subjects = uploaded_df[uploaded_df.student == student]["subject"].nunique()

                        total_subjects = len(
                            set(marks[marks.student == student]["subject"])
                            | set(uploaded_df[uploaded_df.student == student]["subject"])
                        )

                        if total_subjects > 8:
                            st.error(f"{student} exceeds 8 subjects limit ❌")
                            error_flag = True

                    if not error_flag:

                        # Remove duplicates for same student/subject
                        for _, row in uploaded_df.iterrows():
                            marks = marks[
                                ~((marks.student == row["student"]) &
                                  (marks.subject == row["subject"]))
                            ]

                        marks = pd.concat([marks, uploaded_df], ignore_index=True)
                        save(marks, MARKS_FILE)

                        # Update results
                        for student in uploaded_df["student"].unique():

                            student_marks = marks[marks.student == student]

                            total = student_marks["marks"].sum()
                            average = student_marks["marks"].mean()
                            grade = calculate_grade(average)

                            results = results[results.student != student]

                            new_result = pd.DataFrame(
                                [[student, total, round(average, 2), grade]],
                                columns=results.columns
                            )

                            results = pd.concat([results, new_result], ignore_index=True)

                        save(results, RESULTS_FILE)

                        st.success("All marks saved successfully ✅")
                        st.rerun()

        except Exception as e:
            st.error(f"Error reading file: {e}")

# =====================================================
# STUDENT PANEL
# =====================================================
elif role == "student":

    st.header(f"📊 Results for {user['username']}")

    student_name = user["username"]

    student_marks = marks[marks.student == student_name]
    student_result = results[results.student == student_name]

    if not student_marks.empty:
        st.subheader("Subject Marks")
        st.table(student_marks)
        st.bar_chart(student_marks.set_index("subject")["marks"])

    if not student_result.empty:
        st.metric("Total Marks", student_result.iloc[0]["total_marks"])
        st.metric("Average", student_result.iloc[0]["average"])
        st.metric("Grade", student_result.iloc[0]["grade"])

    if len(student_marks) > 1:
        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values
        model = LinearRegression()
        model.fit(X, y)
        prediction = model.predict([[len(y)]])[0]
        st.info(f"📈 Predicted next mark: {round(prediction,1)}")

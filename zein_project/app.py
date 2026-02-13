import streamlit as st
import pandas as pd
import os
from sklearn.linear_model import LinearRegression
import numpy as np

st.set_page_config(page_title="School System", layout="wide")

# =====================================================
# FILES
# =====================================================
USERS_FILE = "users.csv"
MARKS_FILE = "marks.csv"


# =====================================================
# CREATE FILES FIRST TIME
# =====================================================
if not os.path.exists(USERS_FILE):
    pd.DataFrame([
        ["admin", "12345", "admin"],
        ["teacher1", "1234", "teacher"],
        ["student1", "1234", "student"],
    ], columns=["username", "password", "role"]).to_csv(USERS_FILE, index=False)

if not os.path.exists(MARKS_FILE):
    pd.DataFrame(columns=["student", "subject", "marks"]).to_csv(MARKS_FILE, index=False)


# =====================================================
# LOAD DATA
# =====================================================
users = pd.read_csv(USERS_FILE)
marks = pd.read_csv(MARKS_FILE)


# =====================================================
# SAVE FUNCTIONS
# =====================================================
def save_users(df):
    df.to_csv(USERS_FILE, index=False)


def save_marks(df):
    df.to_csv(MARKS_FILE, index=False)


# =====================================================
# LOGIN SYSTEM
# =====================================================
if "user" not in st.session_state:

    st.title("🎓 School Portal Login")

    tab1, tab2 = st.tabs(["Login", "Forgot Password"])

    # ---------------- LOGIN ----------------
    with tab1:
        username = st.text_input("Username").strip()
        password = st.text_input("Password", type="password").strip()

        if st.button("Login"):

            match = users[
                (users.username.astype(str) == username) &
                (users.password.astype(str) == password)
            ]

            if not match.empty:
                st.session_state.user = match.iloc[0].to_dict()
                st.rerun()
            else:
                st.error("Wrong username or password")

    # ---------------- FORGOT PASSWORD ----------------
    with tab2:
        st.subheader("Security Question")

        u = st.text_input("Enter username").strip()
        answer = st.text_input("Who is zein ?", type="password").strip()

        if st.button("Reset Password"):
            if answer.lower() == "zeinzein":
                st.success("Password reset to 1234")
                users.loc[users.username == u, "password"] = "1234"
                save_users(users)
            else:
                st.error("Wrong answer")

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

    st.header("👨‍💼 Admin Panel - Add Users")

    new_user = st.text_input("Username")
    new_pass = st.text_input("Password")
    new_role = st.selectbox("Role", ["teacher", "student", "admin"])

    if st.button("Add User"):
        users.loc[len(users)] = [new_user, new_pass, new_role]
        save_users(users)
        st.success("User added successfully!")


# =====================================================
# TEACHER PANEL
# =====================================================
elif role == "teacher":

    st.header("📤 Upload Student Marks")

    student = st.text_input("Student name")
    subject = st.text_input("Subject")
    mark = st.number_input("Marks", 0, 100)

    if st.button("Save Mark"):
        marks.loc[len(marks)] = [student, subject, mark]
        save_marks(marks)
        st.success("Saved!")


# =====================================================
# STUDENT PANEL
# =====================================================
elif role == "student":

    st.header("📊 My Marks")

    student_marks = marks[marks.student == user["username"]]

    if student_marks.empty:
        st.info("No marks yet")
    else:
        st.dataframe(student_marks)

        # Chart
        st.bar_chart(student_marks.set_index("subject")["marks"])

        # ---------------- AI PREDICTION ----------------
        st.subheader("🤖 AI Performance Prediction")

        X = np.arange(len(student_marks)).reshape(-1, 1)
        y = student_marks["marks"].values

        if len(y) > 1:
            model = LinearRegression()
            model.fit(X, y)
            next_mark = model.predict([[len(y)]])[0]
            st.success(f"Predicted next mark: {round(next_mark, 1)}")
        else:
            st.info("Need more marks for prediction")

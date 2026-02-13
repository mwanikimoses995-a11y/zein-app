import streamlit as st
import pandas as pd

# =====================================
# FILE SETUP
# =====================================
USERS_FILE = "users.csv"
MARKS_FILE = "marks.csv"


def load_users():
    try:
        return pd.read_csv(USERS_FILE)
    except:
        df = pd.DataFrame(columns=["username", "password", "role"])
        df.to_csv(USERS_FILE, index=False)
        return df


def load_marks():
    try:
        return pd.read_csv(MARKS_FILE)
    except:
        df = pd.DataFrame(columns=["student", "subject", "marks"])
        df.to_csv(MARKS_FILE, index=False)
        return df


users = load_users()
marks = load_marks()

# =====================================
# APP TITLE
# =====================================
st.title("📚 Zein System")

# =====================================
# LOGIN SYSTEM
# =====================================
if "user" not in st.session_state:

    st.subheader("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        match = users[
            (users.username == username) &
            (users.password == password)
        ]

        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Wrong username or password")

    st.stop()


# =====================================
# AFTER LOGIN
# =====================================
user = st.session_state.user
role = user["role"]

st.sidebar.success(f"Logged in as {user['username']} ({role})")

if st.sidebar.button("Logout"):
    del st.session_state.user
    st.rerun()


# =====================================
# ADMIN DASHBOARD
# =====================================
if role == "admin":

    st.header("🛠 Admin Panel")

    st.subheader("Add New User")

    new_username = st.text_input("Username")
    new_password = st.text_input("Password")
    new_role = st.selectbox("Role", ["admin", "teacher", "student"])

    if st.button("Create User"):
        users.loc[len(users)] = [new_username, new_password, new_role]
        users.to_csv(USERS_FILE, index=False)
        st.success("User created successfully")
        st.rerun()

    st.subheader("All Users")
    st.dataframe(users)


# =====================================
# TEACHER DASHBOARD
# =====================================
elif role == "teacher":

    st.header("👩‍🏫 Teacher Panel")

    student = st.text_input("Student name")
    subject = st.text_input("Subject")
    score = st.number_input("Marks", 0, 100)

    if st.button("Save Marks"):
        marks.loc[len(marks)] = [student, subject, score]
        marks.to_csv(MARKS_FILE, index=False)
        st.success("Marks saved")

    st.subheader("All Marks")
    st.dataframe(marks)


# =====================================
# STUDENT DASHBOARD
# =====================================
elif role == "student":

    st.header("🎓 Student Panel")

    student_data = marks[marks.student == user["username"]]

    if student_data.empty:
        st.info("No marks uploaded yet")
    else:
        st.dataframe(student_data)

        # Chart
        st.subheader("📊 Performance Chart")
        st.bar_chart(student_data.set_index("subject")["marks"])

        # AI Tip
        st.subheader("🤖 AI Study Tip")

        avg = student_data["marks"].mean()

        if avg >= 80:
            msg = "Excellent work! Keep it up 💪"
        elif avg >= 50:
            msg = "Good job. Practice more to improve 👍"
        else:
            msg = "Study harder and revise daily 📚"

        st.write(f"Average Score: *{round(avg,2)}*")
        st.success(msg)

import streamlit as st
import sqlite3
import pandas as pd

# -------------------- CONFIG --------------------
st.set_page_config(page_title="Attendance & Performance System", layout="wide")

DB_NAME = "database.db"

# -------------------- DATABASE --------------------
def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT NOT NULL,
        role TEXT NOT NULL,
        subject TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS records (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student TEXT NOT NULL,
        subject TEXT NOT NULL,
        attendance REAL NOT NULL,
        score REAL NOT NULL
    )
    """)

    # default admin
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute(
            "INSERT INTO users VALUES (?,?,?,?)",
            ("admin", "admin", "admin", None)
        )

    conn.commit()
    conn.close()

init_db()

# -------------------- AUTH --------------------
def login(username, password):
    conn = get_connection()
    df = pd.read_sql(
        "SELECT * FROM users WHERE username=? AND password=?",
        conn,
        params=(username, password)
    )
    conn.close()
    return None if df.empty else df.iloc[0].to_dict()

# -------------------- LOGIN UI --------------------
if "user" not in st.session_state:
    st.title("🔐 Login")

    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")

    if submit:
        user = login(username, password)
        if user:
            st.session_state.user = user
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.stop()

user = st.session_state.user

# -------------------- ADMIN --------------------
if user["role"] == "admin":
    st.title("🛠️ Admin Dashboard")

    tab1, tab2, tab3 = st.tabs(["Add Teacher", "Add Student", "Analytics"])

    # ---- ADD TEACHER ----
    with tab1:
        subject = st.text_input("Subject Name (Teacher Username)")
        if st.button("Add Teacher"):
            if subject:
                try:
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO users VALUES (?,?,?,?)",
                        (subject, "1234", "teacher", subject)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Teacher '{subject}' added")
                except sqlite3.IntegrityError:
                    st.error("Teacher already exists")

    # ---- ADD STUDENT ----
    with tab2:
        student = st.text_input("Student Name (Username)")
        if st.button("Add Student"):
            if student:
                try:
                    conn = get_connection()
                    conn.execute(
                        "INSERT INTO users VALUES (?,?,?,?)",
                        (student, "1234", "student", None)
                    )
                    conn.commit()
                    conn.close()
                    st.success(f"Student '{student}' added")
                except sqlite3.IntegrityError:
                    st.error("Student already exists")

    # ---- ANALYTICS ----
    with tab3:
        conn = get_connection()
        df = pd.read_sql("SELECT * FROM records", conn)
        conn.close()

        if len(df) > 1:
            corr = df["attendance"].corr(df["score"])
            st.metric("Attendance–Performance Correlation", round(corr, 3))
            st.scatter_chart(df, x="attendance", y="score")
        else:
            st.info("Not enough data for correlation")

# -------------------- TEACHER --------------------
elif user["role"] == "teacher":
    st.title(f"📚 Teacher Dashboard — {user['subject']}")

    with st.form("entry_form"):
        student = st.text_input("Student Name")
        attendance = st.number_input("Attendance (%)", 0.0, 100.0)
        score = st.number_input("Performance Score", 0.0, 100.0)
        submit = st.form_submit_button("Save")

    if submit and student:
        conn = get_connection()
        conn.execute(
            "INSERT INTO records (student, subject, attendance, score) VALUES (?,?,?,?)",
            (student, user["subject"], attendance, score)
        )
        conn.commit()
        conn.close()
        st.success("Record saved")

    conn = get_connection()
    df = pd.read_sql(
        "SELECT student, attendance, score FROM records WHERE subject=?",
        conn,
        params=(user["subject"],)
    )
    conn.close()

    st.dataframe(df)

# -------------------- STUDENT --------------------
elif user["role"] == "student":
    st.title(f"🎓 Student Dashboard — {user['username']}")

    conn = get_connection()
    df = pd.read_sql(
        "SELECT subject, attendance, score FROM records WHERE student=?",
        conn,
        params=(user["username"],)
    )
    conn.close()

    if df.empty:
        st.info("No records yet")
    else:
        st.dataframe(df)
        st.metric("Average Attendance", f"{df.attendance.mean():.1f}%")
        st.metric("Average Score", f"{df.score.mean():.1f}")

# -------------------- LOGOUT --------------------
st.sidebar.button("Logout", on_click=lambda: st.session_state.clear())

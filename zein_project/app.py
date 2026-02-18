import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config("Zein School ERP AI", layout="wide")

# =========================
# FILES
# =========================
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

TERMS = ["Term 1", "Term 2", "Term 3"]
TERM_INDEX = {"Term 1": 1, "Term 2": 2, "Term 3": 3}
CLASSES = ["Form 1", "Form 2", "Form 3", "Form 4"]

COMPULSORY = ["English", "Mathematics", "Kiswahili", "Chemistry", "Biology"]
HUMANITIES = ["History", "Geography"]
SCIENCE_REL = ["CRE", "Physics"]
TECHNICAL = ["Business", "Computer", "Agriculture"]

# =========================
# UTILITIES
# =========================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def ensure_csv(file, cols, default=None):
    if not os.path.exists(file):
        pd.DataFrame(default or [], columns=cols).to_csv(file, index=False)

def load(file):
    return pd.read_csv(file)

def save(df, file):
    df.to_csv(file, index=False)

def grade(avg):
    if avg >= 80: return "A"
    if avg >= 70: return "B"
    if avg >= 60: return "C"
    if avg >= 50: return "D"
    return "E"

# =========================
# AI – ZEIN
# =========================
def zein_predict(scores, terms):
    """
    Simple linear trend prediction.
    Stable, explainable, no ML dependency.
    """
    if len(scores) < 2:
        return scores[-1]

    x = np.array(terms)
    y = np.array(scores)

    coef = np.polyfit(x, y, 1)
    next_term = max(terms) + 1
    pred = coef[0] * next_term + coef[1]
    return max(0, min(100, pred))

# =========================
# CREATE FILES
# =========================
ensure_csv(
    USERS_FILE,
    ["username","password","role","subject"],
    [["admin", hash_password("1234"), "admin", ""]]
)
ensure_csv(STUDENTS_FILE, ["student","class"])
ensure_csv(MARKS_FILE, ["student","class","term","subject","marks"])
ensure_csv(ATTENDANCE_FILE, ["student","class","term","attendance"])

users = load(USERS_FILE)
students = load(STUDENTS_FILE)
marks = load(MARKS_FILE)
attendance = load(ATTENDANCE_FILE)

# =========================
# LOGIN
# =========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        m = users[(users.username==u) & (users.password==hash_password(p))]
        if not m.empty:
            st.session_state.user = m.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid login")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 {user['username']} ({role})")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN
# =========================
if role == "admin":
    st.header("🛠 Admin Dashboard")

    tab1, tab2 = st.tabs(["Add Users", "Remove Users"])

    with tab1:
        st.subheader("➕ Add Student")
        name = st.text_input("Student Full Name")
        cls = st.selectbox("Class", CLASSES)
        if st.button("Create Student"):
            if name and name not in users.username.values:
                users.loc[len(users)] = [name, hash_password("1234"), "student", ""]
                students.loc[len(students)] = [name, cls]
                save(users, USERS_FILE)
                save(students, STUDENTS_FILE)
                st.success("Student created (password = 1234)")

        st.subheader("➕ Add Teacher")
        subject = st.text_input("Subject")
        number = st.text_input("Number")
        if st.button("Create Teacher"):
            username = f"{subject.lower()}{number}"
            if username not in users.username.values:
                users.loc[len(users)] = [username, hash_password("1234"), "teacher", subject]
                save(users, USERS_FILE)
                st.success(f"Teacher created ({username})")

    with tab2:
        removable = users[users.username!="admin"]["username"].tolist()
        target = st.selectbox("Select User", removable)
        if st.button("Delete User"):
            users = users[users.username!=target]
            students = students[students.student!=target]
            marks = marks[marks.student!=target]
            attendance = attendance[attendance.student!=target]
            save(users, USERS_FILE)
            save(students, STUDENTS_FILE)
            save(marks, MARKS_FILE)
            save(attendance, ATTENDANCE_FILE)
            st.success("User removed")

# =========================
# TEACHER
# =========================
elif role == "teacher":
    st.header(f"👩‍🏫 Teacher Dashboard — {user['subject']}")

    cls = st.selectbox("Class", CLASSES)
    term = st.selectbox("Term", TERMS)
    term_id = TERM_INDEX[term]

    class_students = students[students["class"]==cls]["student"].tolist()
    if not class_students:
        st.warning("No students")
        st.stop()

    st.subheader("📚 Subject Selection Rules")
    hum = st.selectbox("Humanity (ONE)", HUMANITIES)
    sci = st.selectbox("CRE / Physics (ONE)", SCIENCE_REL)
    tech = st.selectbox("Technical (ONE)", TECHNICAL)

    subjects = COMPULSORY + [hum, sci, tech]

    for subj in subjects:
        st.markdown(f"### {subj}")
        table = pd.DataFrame({
            "student": class_students,
            "marks": [
                marks[(marks.student==s)&(marks.term==term)&(marks.subject==subj)]["marks"].values[0]
                if not marks[(marks.student==s)&(marks.term==term)&(marks.subject==subj)].empty else 0
                for s in class_students
            ]
        })

        edited = st.data_editor(table, num_rows="fixed", key=subj)

        if st.button(f"Save {subj}", key=f"save_{subj}"):
            marks = marks[~((marks.term==term)&(marks.subject==subj)&
                            (marks.student.isin(class_students)))]
            for _, r in edited.iterrows():
                marks.loc[len(marks)] = {
                    "student": r.student,
                    "class": cls,
                    "term": term,
                    "subject": subj,
                    "marks": r.marks
                }
            save(marks, MARKS_FILE)
            st.success(f"{subj} saved")

    st.subheader("📋 Attendance (%)")
    att = pd.DataFrame({
        "student": class_students,
        "attendance": [
            attendance[(attendance.student==s)&(attendance.term==term)]["attendance"].values[0]
            if not attendance[(attendance.student==s)&(attendance.term==term)].empty else 0
            for s in class_students
        ]
    })

    att_edit = st.data_editor(att, num_rows="fixed")

    if st.button("Save Attendance"):
        attendance = attendance[~((attendance.term==term)&
                                  (attendance.student.isin(class_students)))]
        for _, r in att_edit.iterrows():
            attendance.loc[len(attendance)] = {
                "student": r.student,
                "class": cls,
                "term": term,
                "attendance": r.attendance
            }
        save(attendance, ATTENDANCE_FILE)
        st.success("Attendance saved")

# =========================
# STUDENT + ZEIN AI
# =========================
elif role == "student":
    st.header("📊 Student Dashboard")

    sm = marks[marks.student==user["username"]]
    sa = attendance[attendance.student==user["username"]]

    if sm.empty:
        st.info("No records yet")
        st.stop()

    st.subheader("📈 Performance Trend")
    avg = sm.groupby("term")["marks"].mean().reset_index()
    fig, ax = plt.subplots()
    ax.plot(avg.term, avg.marks, marker="o")
    ax.set_ylim(0,100)
    st.pyplot(fig)

    overall = sm.marks.mean()
    st.metric("Overall Average", round(overall,2))
    st.metric("Overall Grade", grade(overall))

    st.subheader("🤖 ZEIN AI – Next Term Prediction")

    preds = []
    for subj in sm.subject.unique():
        d = sm[sm.subject==subj].copy()
        d["t"] = d.term.map(TERM_INDEX)
        pred = zein_predict(d.marks.tolist(), d.t.tolist())
        preds.append({"Subject": subj, "Predicted Mark": round(pred,2)})

    pdf = pd.DataFrame(preds)
    st.dataframe(pdf)

    mean_pred = pdf["Predicted Mark"].mean()
    st.metric("Predicted Mean", round(mean_pred,2))
    st.metric("Predicted Grade", grade(mean_pred))

    if not sa.empty:
        st.subheader("📊 Attendance vs Performance")
        merged = pd.merge(sm, sa, on=["student","class","term"])
        st.scatter_chart(merged, x="attendance", y="marks")

import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School ERP AI", layout="wide")

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
# UTILITIES & REPAIR
# =========================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_data(file, expected_cols, default_rows=None):
    """Loads CSV and ensures headers are correct to prevent KeyErrors."""
    if not os.path.exists(file):
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    
    df = pd.read_csv(file)
    # Check if any expected column is missing
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        for c in missing:
            df[c] = "" if "marks" not in c and "attendance" not in c else 0
        df.to_csv(file, index=False)
    return df

def save(df, file):
    df.to_csv(file, index=False)

def grade(avg):
    if avg >= 80: return "A"
    if avg >= 70: return "B"
    if avg >= 60: return "C"
    if avg >= 50: return "D"
    return "E"

def zein_predict(scores, terms):
    if len(scores) < 2:
        return scores[-1] if scores else 0
    try:
        coef = np.polyfit(terms, scores, 1)
        next_term = max(terms) + 1
        pred = coef[0] * next_term + coef[1]
        return max(0, min(100, pred))
    except:
        return scores[-1]

# =========================
# INITIALIZE DATA
# =========================
users = load_data(USERS_FILE, ["username", "password", "role"], [["admin", hash_password("1234"), "admin"]])
students = load_data(STUDENTS_FILE, ["student", "class"])
marks = load_data(MARKS_FILE, ["student", "class", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["student", "class", "term", "attendance"])

# =========================
# LOGIN
# =========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        match = users[(users.username == u) & (users.password == hash_password(p))]
        if not match.empty:
            st.session_state.user = match.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid credentials")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.title("Zein ERP")
st.sidebar.write(f"👤 **{user['username']}**")
st.sidebar.info(f"Role: {role.upper()}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN: USER MGMT
# =========================
if role == "admin":
    st.header("🛠 Admin Dashboard")
    t1, t2 = st.tabs(["Add Accounts", "System Clean-up"])

    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Add Student")
            s_name = st.text_input("Full Name")
            s_cls = st.selectbox("Assign Class", CLASSES)
            if st.button("Create Student"):
                if s_name and s_name not in users.username.values:
                    users.loc[len(users)] = [s_name, hash_password("1234"), "student"]
                    students.loc[len(students)] = [s_name, s_cls]
                    save(users, USERS_FILE); save(students, STUDENTS_FILE)
                    st.success("Student added (Pass: 1234)")
                else: st.error("Name exists or empty")

        with col2:
            st.subheader("Add Teacher")
            t_name = st.text_input("Teacher Username")
            if st.button("Create Teacher"):
                if t_name and t_name not in users.username.values:
                    users.loc[len(users)] = [t_name, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success(f"Teacher {t_name} added")

    with t2:
        removable = users[users.username != "admin"]["username"].tolist()
        target = st.selectbox("Select User to Remove", removable)
        if st.button("🔥 Permanently Delete User"):
            users = users[users.username != target]
            students = students[students.student != target]
            marks = marks[marks.student != target]
            attendance = attendance[attendance.student != target]
            save(users, USERS_FILE); save(students, STUDENTS_FILE)
            save(marks, MARKS_FILE); save(attendance, ATTENDANCE_FILE)
            st.rerun()

# =========================
# TEACHER: MARKS ENTRY
# =========================
elif role == "teacher":
    st.header("👩‍🏫 Academic Records Management")
    
    col_x, col_y = st.columns(2)
    sel_cls = col_x.selectbox("Target Class", CLASSES)
    sel_term = col_y.selectbox("Target Term", TERMS)

    class_students = students[students["class"] == sel_cls]["student"].tolist()
    
    if not class_students:
        st.warning(f"No students found in {sel_cls}. Add them in Admin panel.")
    else:
        tab_m, tab_a = st.tabs(["Subject Grading", "Attendance Records"])

        with tab_m:
            st.caption("Choose the elective subjects for this class:")
            c1, c2, c3 = st.columns(3)
            h_sub = c1.selectbox("Humanity", HUMANITIES)
            s_sub = c2.selectbox("Science", SCIENCE_REL)
            t_sub = c3.selectbox("Technical", TECHNICAL)
            
            all_subs = COMPULSORY + [h_sub, s_sub, t_sub]
            
            for subj in all_subs:
                with st.expander(f"📝 {subj} Marks", expanded=False):
                    # Fetch existing marks for these students
                    m_data = []
                    for s in class_students:
                        row = marks[(marks.student == s) & (marks.term == sel_term) & (marks.subject == subj)]
                        m_data.append(row["marks"].values[0] if not row.empty else 0)
                    
                    edit_df = pd.DataFrame({"Student": class_students, "Marks": m_data})
                    result_df = st.data_editor(edit_df, key=f"ed_{subj}_{sel_cls}", use_container_width=True)
                    
                    if st.button(f"Save {subj}", key=f"sav_{subj}"):
                        # Clear old entries for this specific set
                        marks = marks[~((marks.term == sel_term) & (marks.subject == subj) & (marks.student.isin(class_students)))]
                        # Add new
                        for _, r in result_df.iterrows():
                            marks.loc[len(marks)] = [r.Student, sel_cls, sel_term, subj, r.Marks]
                        save(marks, MARKS_FILE)
                        st.toast(f"Saved {subj}!")

        with tab_a:
            st.subheader("Attendance (%)")
            att_data = []
            for s in class_students:
                row = attendance[(attendance.student == s) & (attendance.term == sel_term)]
                att_data.append(row["attendance"].values[0] if not row.empty else 0)
            
            att_edit_df = pd.DataFrame({"Student": class_students, "Attendance": att_data})
            final_att = st.data_editor(att_edit_df, use_container_width=True)
            
            if st.button("Save Attendance"):
                attendance = attendance[~((attendance.term == sel_term) & (attendance.student.isin(class_students)))]
                for _, r in final_att.iterrows():
                    attendance.loc[len(attendance)] = [r.Student, sel_cls, sel_term, r.Attendance]
                save(attendance, ATTENDANCE_FILE)
                st.success("Attendance Updated")

# =========================
# STUDENT: AI INSIGHTS
# =========================
elif role == "student":
    st.header(f"📊 Progress Report: {user['username']}")
    
    my_marks = marks[marks.student == user["username"]]
    my_att = attendance[attendance.student == user["username"]]

    if my_marks.empty:
        st.info("No marks recorded yet. Check back after your teacher updates them.")
    else:
        # Metrics
        m_avg = my_marks.marks.mean()
        c1, c2, c3 = st.columns(3)
        c1.metric("Overall Average", f"{round(m_avg,1)}%")
        c2.metric("Current Grade", grade(m_avg))
        if not my_att.empty:
            c3.metric("Last Attendance", f"{my_att.iloc[-1]['attendance']}%")

        # Trend Chart
        st.subheader("Performance over Terms")
        trend = my_marks.groupby("term")["marks"].mean().reindex(TERMS).dropna()
        st.line_chart(trend)

        # Zein AI
        st.divider()
        st.subheader("🤖 Zein AI - Term Prediction")
        
        preds = []
        for s in my_marks.subject.unique():
            df_s = my_marks[my_marks.subject == s].copy()
            df_s["t_id"] = df_s.term.map(TERM_INDEX)
            val = zein_predict(df_s.marks.tolist(), df_s.t_id.tolist())
            preds.append({"Subject": s, "Predicted Mark": round(val, 1)})
        
        st.table(pd.DataFrame(preds))
        p_avg = sum(p["Predicted Mark"] for p in preds) / len(preds)
        st.write(f"**Zein AI Prediction:** You are on track for a **{grade(p_avg)}** next term.")

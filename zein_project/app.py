import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Zein School ERP AI", layout="wide")

# =========================
# FILES & CONFIG
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

def zein_predict(scores, terms):
    if len(scores) < 2:
        return scores[-1] if scores else 0
    x = np.array(terms)
    y = np.array(scores)
    coef = np.polyfit(x, y, 1)
    next_term = max(terms) + 1
    pred = coef[0] * next_term + coef[1]
    return max(0, min(100, pred))

# =========================
# INITIALIZE DATABASE
# =========================
ensure_csv(USERS_FILE, ["username","password","role"], [["admin", hash_password("1234"), "admin"]])
ensure_csv(STUDENTS_FILE, ["student","class"])
ensure_csv(MARKS_FILE, ["student","class","term","subject","marks"])
ensure_csv(ATTENDANCE_FILE, ["student","class","term","attendance"])

users = load(USERS_FILE)
students = load(STUDENTS_FILE)
marks = load(MARKS_FILE)
attendance = load(ATTENDANCE_FILE)

# =========================
# LOGIN SYSTEM
# =========================
if "user" not in st.session_state:
    st.title("🎓 Zein School ERP Login")
    u = st.text_input("Username")
    p = st.text_input("Password", type="password")
    if st.button("Login"):
        m = users[(users.username == u) & (users.password == hash_password(p))]
        if not m.empty:
            st.session_state.user = m.iloc[0].to_dict()
            st.rerun()
        else:
            st.error("Invalid login credentials")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.write(f"👤 **{user['username']}**")
st.sidebar.write(f"Role: {role.capitalize()}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN DASHBOARD
# =========================
if role == "admin":
    st.header("🛠 Admin Control Panel")
    t1, t2 = st.tabs(["Manage Users", "System View"])

    with t1:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("➕ Add Student")
            s_name = st.text_input("Student Name")
            s_cls = st.selectbox("Assign Class", CLASSES)
            if st.button("Register Student"):
                if s_name and s_name not in users.username.values:
                    users.loc[len(users)] = [s_name, hash_password("1234"), "student"]
                    students.loc[len(students)] = [s_name, s_cls]
                    save(users, USERS_FILE); save(students, STUDENTS_FILE)
                    st.success(f"Student {s_name} added.")

        with col2:
            st.subheader("➕ Add Staff")
            t_name = st.text_input("Teacher Username")
            if st.button("Register Teacher"):
                if t_name and t_name not in users.username.values:
                    users.loc[len(users)] = [t_name, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success(f"Teacher {t_name} added.")

        st.divider()
        st.subheader("🗑 Delete User")
        removable = users[users.username != "admin"]["username"].tolist()
        target = st.selectbox("Select User to Remove", removable)
        if st.button("Confirm Deletion", font_variant="small-caps"):
            users = users[users.username != target]
            students = students[students.student != target]
            marks = marks[marks.student != target]
            attendance = attendance[attendance.student != target]
            save(users, USERS_FILE); save(students, STUDENTS_FILE); save(marks, MARKS_FILE); save(attendance, ATTENDANCE_FILE)
            st.rerun()

# =========================
# TEACHER DASHBOARD (Generalized)
# =========================
elif role == "teacher":
    st.header("👩‍🏫 Academic Management")
    
    col_a, col_b = st.columns(2)
    with col_a:
        sel_cls = st.selectbox("Select Class", CLASSES)
    with col_b:
        sel_term = st.selectbox("Select Term", TERMS)

    class_list = students[students["class"] == sel_cls]["student"].tolist()
    
    if not class_list:
        st.warning(f"No students registered in {sel_cls}")
    else:
        tab_marks, tab_att = st.tabs(["Enter Marks", "Enter Attendance"])

        with tab_marks:
            st.info("Select elective subjects for this class to update records.")
            c1, c2, c3 = st.columns(3)
            h_sub = c1.selectbox("Humanity", HUMANITIES)
            s_sub = c2.selectbox("Science Elective", SCIENCE_REL)
            t_sub = c3.selectbox("Technical", TECHNICAL)
            
            active_subjects = COMPULSORY + [h_sub, s_sub, t_sub]
            
            for subj in active_subjects:
                with st.expander(f"Edit Marks: {subj}", expanded=False):
                    # Fetch existing marks or default to 0
                    current_marks = []
                    for s in class_list:
                        match = marks[(marks.student == s) & (marks.term == sel_term) & (marks.subject == subj)]
                        current_marks.append(match["marks"].values[0] if not match.empty else 0)
                    
                    df_edit = pd.DataFrame({"Student": class_list, "Marks": current_marks})
                    edited_df = st.data_editor(df_edit, key=f"editor_{subj}_{sel_cls}", use_container_width=True)
                    
                    if st.button(f"Update {subj} Marks", key=f"btn_{subj}"):
                        # Remove old entries for this specific class/term/subject
                        marks = marks[~((marks.term == sel_term) & (marks.subject == subj) & (marks.student.isin(class_list)))]
                        # Add new entries
                        for _, row in edited_df.iterrows():
                            marks.loc[len(marks)] = [row.Student, sel_cls, sel_term, subj, row.Marks]
                        save(marks, MARKS_FILE)
                        st.success(f"Records updated for {subj}")

        with tab_att:
            st.subheader("Attendance Percentage")
            current_att = []
            for s in class_list:
                match = attendance[(attendance.student == s) & (attendance.term == sel_term)]
                current_att.append(match["attendance"].values[0] if not match.empty else 0)
            
            df_att = pd.DataFrame({"Student": class_list, "Attendance %": current_att})
            edited_att = st.data_editor(df_att, use_container_width=True)
            
            if st.button("Save Attendance"):
                attendance = attendance[~((attendance.term == sel_term) & (attendance.student.isin(class_list)))]
                for _, row in edited_att.iterrows():
                    attendance.loc[len(attendance)] = [row.Student, sel_cls, sel_term, row["Attendance %"]]
                save(attendance, ATTENDANCE_FILE)
                st.success("Attendance saved.")

# =========================
# STUDENT DASHBOARD
# =========================
elif role == "student":
    st.header(f"📊 Report Card: {user['username']}")
    
    s_marks = marks[marks.student == user["username"]]
    s_att = attendance[attendance.student == user["username"]]

    if s_marks.empty:
        st.info("No academic records found yet.")
    else:
        # Performance Analytics
        avg_per_term = s_marks.groupby("term")["marks"].mean().reindex(TERMS).fillna(0)
        
        col1, col2, col3 = st.columns(3)
        overall_avg = s_marks.marks.mean()
        col1.metric("Mean Score", f"{round(overall_avg, 2)}%")
        col2.metric("Mean Grade", grade(overall_avg))
        if not s_att.empty:
            col3.metric("Avg Attendance", f"{round(s_att.attendance.mean(), 1)}%")

        st.subheader("Performance Trend")
        st.line_chart(avg_per_term)

        # Zein AI Prediction
        st.subheader("🤖 Zein AI: Predicted Next Term Results")
        predictions = []
        for subj in s_marks.subject.unique():
            subj_df = s_marks[s_marks.subject == subj].copy()
            subj_df["t_val"] = subj_df.term.map(TERM_INDEX)
            p_score = zein_predict(subj_df.marks.tolist(), subj_df.t_val.tolist())
            predictions.append({"Subject": subj, "Predicted Score": round(p_score, 1)})
        
        pred_df = pd.DataFrame(predictions)
        st.table(pred_df)
        
        p_mean = pred_df["Predicted Score"].mean()
        st.write(f"**Predicted Next Term Grade:** {grade(p_mean)} ({round(p_mean, 2)})")

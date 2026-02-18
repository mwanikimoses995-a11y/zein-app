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
# UTILITIES & DATA REPAIR
# =========================
def hash_password(p):
    return hashlib.sha256(p.encode()).hexdigest()

def load_data(file, expected_cols, default_rows=None):
    if not os.path.exists(file):
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    if list(df.columns) != expected_cols:
        df = df.reindex(columns=expected_cols).fillna(0 if "marks" in str(expected_cols) else "")
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
    if len(scores) < 2: return scores[-1] if scores else 0
    try:
        coef = np.polyfit(terms, scores, 1)
        next_term = max(terms) + 1
        return max(0, min(100, coef[0] * next_term + coef[1]))
    except: return scores[-1]

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
        else: st.error("Invalid credentials")
    st.stop()

user = st.session_state.user
role = user["role"]

st.sidebar.title("Zein ERP")
st.sidebar.write(f"👤 **{user['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN
# =========================
if role == "admin":
    st.header("🛠 Admin Dashboard")
    t1, t2 = st.tabs(["Add Accounts", "System Clean-up"])
    with t1:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("Add Student")
            s_name = st.text_input("Full Name")
            s_cls = st.selectbox("Assign Class", CLASSES)
            if st.button("Create Student"):
                if s_name and s_name not in users.username.values:
                    users.loc[len(users)] = [s_name, hash_password("1234"), "student"]
                    students.loc[len(students)] = [s_name, s_cls]
                    save(users, USERS_FILE); save(students, STUDENTS_FILE)
                    st.success(f"Added {s_name}")
                else: st.error("Invalid entry")
        with c2:
            st.subheader("Add Teacher")
            t_name = st.text_input("Teacher Username")
            if st.button("Create Teacher"):
                if t_name and t_name not in users.username.values:
                    users.loc[len(users)] = [t_name, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success(f"Added {t_name}")
    with t2:
        target = st.selectbox("Select User to Remove", users[users.username != "admin"]["username"].tolist())
        if st.button("🔥 Delete User"):
            users = users[users.username != target]
            students = students[students.student != target]
            marks = marks[marks.student != target]
            attendance = attendance[attendance.student != target]
            save(users, USERS_FILE); save(students, STUDENTS_FILE); save(marks, MARKS_FILE); save(attendance, ATTENDANCE_FILE)
            st.rerun()

# =========================
# TEACHER (Updated with Student Selector)
# =========================
elif role == "teacher":
    st.header("👩‍🏫 Academic Management")
    
    col1, col2, col3 = st.columns(3)
    sel_cls = col1.selectbox("Select Class", CLASSES)
    sel_term = col2.selectbox("Select Term", TERMS)
    
    # Filter students by the selected class
    class_students = students[students["class"] == sel_cls]["student"].tolist()
    
    if not class_students:
        st.warning(f"No students found in {sel_cls}.")
    else:
        # NEW: Student Selector for targeted management
        sel_student = col3.selectbox("Target Student", ["-- All Students --"] + class_students)
        
        tab_m, tab_a = st.tabs(["Subject Grading", "Attendance"])

        with tab_m:
            # Elective Selection
            c_h, c_s, c_t = st.columns(3)
            h_sub = c_h.selectbox("Humanity", HUMANITIES)
            s_sub = c_s.selectbox("Science", SCIENCE_REL)
            t_sub = c_t.selectbox("Technical", TECHNICAL)
            all_subs = COMPULSORY + [h_sub, s_sub, t_sub]

            if sel_student == "-- All Students --":
                # Bulk View
                for subj in all_subs:
                    with st.expander(f"Bulk Edit: {subj}"):
                        m_list = [marks[(marks.student==s)&(marks.term==sel_term)&(marks.subject==subj)]["marks"].values[0] 
                                  if not marks[(marks.student==s)&(marks.term==sel_term)&(marks.subject==subj)].empty else 0 for s in class_students]
                        df_edit = pd.DataFrame({"Student": class_students, "Marks": m_list})
                        res = st.data_editor(df_edit, key=f"bulk_{subj}")
                        if st.button(f"Save {subj} for All", key=f"btn_{subj}"):
                            marks = marks[~((marks.term==sel_term)&(marks.subject==subj)&(marks.student.isin(class_students)))]
                            for _, r in res.iterrows():
                                marks.loc[len(marks)] = [r.Student, sel_cls, sel_term, subj, r.Marks]
                            save(marks, MARKS_FILE); st.toast(f"{subj} Updated")
            else:
                # Individual Student View
                st.subheader(f"Grading: {sel_student}")
                indiv_data = []
                for subj in all_subs:
                    val = marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==subj)]["marks"].values[0] if not marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==subj)].empty else 0
                    indiv_data.append({"Subject": subj, "Marks": val})
                
                df_indiv = pd.DataFrame(indiv_data)
                res_indiv = st.data_editor(df_indiv, use_container_width=True, key="indiv_editor")
                
                if st.button(f"Save Marks for {sel_student}"):
                    # Remove all marks for this student/term across ALL subjects being edited
                    marks = marks[~((marks.student==sel_student)&(marks.term==sel_term)&(marks.subject.isin(all_subs)))]
                    for _, r in res_indiv.iterrows():
                        marks.loc[len(marks)] = [sel_student, sel_cls, sel_term, r.Subject, r.Marks]
                    save(marks, MARKS_FILE); st.success(f"Updated {sel_student}")

        with tab_a:
            if sel_student == "-- All Students --":
                att_list = [attendance[(attendance.student==s)&(attendance.term==sel_term)]["attendance"].values[0] 
                            if not attendance[(attendance.student==s)&(attendance.term==sel_term)].empty else 0 for s in class_students]
                df_att = pd.DataFrame({"Student": class_students, "Attendance": att_list})
                res_att = st.data_editor(df_att)
                if st.button("Save All Attendance"):
                    attendance = attendance[~((attendance.term==sel_term)&(attendance.student.isin(class_students)))]
                    for _, r in res_att.iterrows():
                        attendance.loc[len(attendance)] = [r.Student, sel_cls, sel_term, r.Attendance]
                    save(attendance, ATTENDANCE_FILE); st.success("Attendance Saved")
            else:
                val_att = attendance[(attendance.student==sel_student)&(attendance.term==sel_term)]["attendance"].values[0] if not attendance[(attendance.student==sel_student)&(attendance.term==sel_term)].empty else 0
                new_att = st.number_input(f"Attendance for {sel_student} (%)", 0, 100, int(val_att))
                if st.button("Save Individual Attendance"):
                    attendance = attendance[~((attendance.student==sel_student)&(attendance.term==sel_term))]
                    attendance.loc[len(attendance)] = [sel_student, sel_cls, sel_term, new_att]
                    save(attendance, ATTENDANCE_FILE); st.success("Attendance Updated")

# =========================
# STUDENT DASHBOARD
# =========================
elif role == "student":
    st.header(f"📊 My Report Card")
    m = marks[marks.student == user["username"]]
    if m.empty: st.info("No marks found.")
    else:
        avg = m.marks.mean()
        st.metric("Mean Grade", f"{grade(avg)} ({round(avg,1)}%)")
        trend = m.groupby("term")["marks"].mean().reindex(TERMS).dropna()
        if not trend.empty: st.line_chart(trend)
        
        st.subheader("🤖 Zein AI Prediction")
        preds = []
        for s in m.subject.unique():
            df_s = m[m.subject == s].copy()
            df_s["t_id"] = df_s.term.map(TERM_INDEX)
            preds.append({"Subject": s, "Predicted": round(zein_predict(df_s.marks.tolist(), df_s.t_id.tolist()), 1)})
        st.table(pd.DataFrame(preds))

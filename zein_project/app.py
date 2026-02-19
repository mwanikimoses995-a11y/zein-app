import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School ERP AI", layout="wide")

USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

TERMS = ["Term 1", "Term 2", "Term 3"]
TERM_ORDER = {term: i for i, term in enumerate(TERMS)}
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
        df = df.reindex(columns=expected_cols).fillna(0)
        df.to_csv(file, index=False)
    return df

def save(df, file):
    df.to_csv(file, index=False)

def get_kcse_grade(marks):
    """Standard KCSE Grading System"""
    if marks >= 80: return "A", 12
    if marks >= 75: return "A-", 11
    if marks >= 70: return "B+", 10
    if marks >= 65: return "B", 9
    if marks >= 60: return "B-", 8
    if marks >= 55: return "C+", 7
    if marks >= 50: return "C", 6
    if marks >= 45: return "C-", 5
    if marks >= 40: return "D+", 4
    if marks >= 35: return "D", 3
    if marks >= 30: return "D-", 2
    return "E", 1

def zein_predict(scores, terms):
    if len(scores) < 2: return scores[-1] if scores else 0
    try:
        coef = np.polyfit(terms, scores, 1)
        next_term = max(terms) + 1
        prediction = coef[0] * next_term + coef[1]
        return max(0, min(100, prediction))
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
# ADMIN / TEACHER SECTIONS (Kept original logic)
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
                    st.success(f"Added {s_name}"); st.rerun()
        with c2:
            st.subheader("Add Teacher")
            t_name = st.text_input("Teacher Username")
            if st.button("Create Teacher"):
                if t_name and t_name not in users.username.values:
                    users.loc[len(users)] = [t_name, hash_password("1234"), "teacher"]
                    save(users, USERS_FILE)
                    st.success(f"Added {t_name}"); st.rerun()
    with t2:
        target_list = users[users.username != "admin"]["username"].tolist()
        if target_list:
            target = st.selectbox("Select User to Remove", target_list)
            if st.button("🔥 Delete User"):
                users = users[users.username != target]
                save(users, USERS_FILE); st.rerun()

elif role == "teacher":
    st.header("👩‍🏫 Academic Management")
    col1, col2, col3 = st.columns(3)
    sel_cls = col1.selectbox("Select Class", CLASSES)
    sel_term = col2.selectbox("Select Term", TERMS)
    class_students = students[students["class"] == sel_cls]["student"].tolist()
    
    if not class_students:
        st.warning(f"No students found in {sel_cls}.")
    else:
        sel_student = col3.selectbox("Target Student", ["-- All Students --"] + class_students)
        tab_m, tab_a = st.tabs(["Subject Grading", "Attendance"])
        with tab_m:
            c_h, c_s, c_t = st.columns(3)
            h_sub = c_h.selectbox("Humanity", HUMANITIES)
            s_sub = c_s.selectbox("Science", SCIENCE_REL)
            t_sub = c_t.selectbox("Technical", TECHNICAL)
            all_subs = COMPULSORY + [h_sub, s_sub, t_sub]
            
            if sel_student == "-- All Students --":
                for subj in all_subs:
                    with st.expander(f"Bulk Edit: {subj}"):
                        m_list = [marks[(marks.student==s)&(marks.term==sel_term)&(marks.subject==subj)]["marks"].values[0] if not marks[(marks.student==s)&(marks.term==sel_term)&(marks.subject==subj)].empty else 0 for s in class_students]
                        res = st.data_editor(pd.DataFrame({"Student": class_students, "Marks": m_list}), key=f"bulk_{subj}")
                        if st.button(f"Save {subj}", key=f"btn_{subj}"):
                            marks = marks[~((marks.term==sel_term)&(marks.subject==subj)&(marks.student.isin(class_students)))]
                            for _, r in res.iterrows():
                                marks.loc[len(marks)] = [r.Student, sel_cls, sel_term, subj, r.Marks]
                            save(marks, MARKS_FILE); st.rerun()
            else:
                indiv_data = [{"Subject": s, "Marks": (marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==s)]["marks"].values[0] if not marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==s)].empty else 0)} for s in all_subs]
                res_indiv = st.data_editor(pd.DataFrame(indiv_data), key="indiv_editor")
                if st.button(f"Save Marks for {sel_student}"):
                    marks = marks[~((marks.student==sel_student)&(marks.term==sel_term))]
                    for _, r in res_indiv.iterrows():
                        marks.loc[len(marks)] = [sel_student, sel_cls, sel_term, r.Subject, r.Marks]
                    save(marks, MARKS_FILE); st.rerun()

# =========================
# STUDENT DASHBOARD (IMPROVED)
# =========================
elif role == "student":
    st.header(f"📊  Performance Analysis: {user['username']}")
    m = marks[marks.student == user["username"]].copy()
    att_df = attendance[attendance.student == user["username"]].copy()
    
    if m.empty:
        st.info("Awaiting academic data entry...")
    else:
        avg_score = m.marks.mean()
        avg_att = att_df.attendance.mean() if not att_df.empty else 0
        current_grade, points = get_kcse_grade(avg_score)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Mean Score", f"{round(avg_score, 1)}%")
        c2.metric("KCSE Grade", current_grade, f"{points} Points")
        c3.metric("Avg. Attendance", f"{round(avg_att, 1)}%")
        
        st.divider()

        # Visual Graphs
        m['term_rank'] = m['term'].map(TERM_ORDER)
        m = m.sort_values('term_rank')
        col_charts_1, col_charts_2 = st.columns(2)

        with col_charts_1:
            st.subheader("📈 Termly Mean Trend")
            trend_data = m.groupby("term", sort=False)["marks"].mean()
            st.bar_chart(trend_data)

        with col_charts_2:
            st.subheader("🎯 Latest Subject Breakdown")
            latest_term = m.iloc[-1]['term']
            latest_marks = m[m.term == latest_term]
            st.bar_chart(latest_marks.set_index("subject")["marks"])

        st.divider()

        # AI Prediction & Intervention Logic
        st.subheader("🤖 Zein AI Future Outlook & Intervention")
        preds = []
        for s in m.subject.unique():
            df_s = m[m.subject == s].copy()
            df_s["t_id"] = df_s.term.map(TERM_INDEX)
            df_s = df_s.sort_values("t_id")
            
            p_val = zein_predict(df_s.marks.tolist(), df_s.t_id.tolist())
            p_grade, _ = get_kcse_grade(p_val)
            
            status = "✅ Stable" if p_val >= df_s.marks.mean() else "⚠️ Declining"
            
            preds.append({
                "Subject": s, 
                "Latest Mark (%)": df_s.marks.iloc[-1],
                "AI Prediction (%)": round(p_val, 1),
                "Projected Grade": p_grade,
                "Status": status
            })
        
        df_preds = pd.DataFrame(preds)

        # Highlight "Declining" status or D/E grades in red
        def style_intervention(row):
            return ['color: red' if row.Status == "⚠️ Declining" or row['Projected Grade'] in ['D', 'D-', 'E'] else 'color: white'] * len(row)

        st.dataframe(df_preds.style.apply(style_intervention, axis=1), use_container_width=True)
        st.caption("Intervention Required for subjects highlighted in RED.")

import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School AI", layout="wide")

USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

MAX_SCHOOL_DAYS = 65 

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
    if len(scores) < 2: 
        return scores[-1] if scores else 0
    try:
        coef = np.polyfit(terms, scores, 1)
        next_term_idx = max(terms) + 1
        prediction = coef[0] * next_term_idx + coef[1]
        return max(0, min(100, prediction))
    except: 
        return scores[-1]

# =========================
# INITIALIZE DATA
# =========================
users = load_data(USERS_FILE, ["username", "password", "role"], [["admin", hash_password("1234"), "admin"]])
students = load_data(STUDENTS_FILE, ["student", "class"])
marks = load_data(MARKS_FILE, ["student", "class", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["student", "class", "term", "days_present"])

# =========================
# LOGIN
# =========================
if "user" not in st.session_state:
    st.title("🎓 Zein School Login")
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

st.sidebar.title("Zein")
st.sidebar.write(f"👤 **{user['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ADMIN SECTION
# =========================
if role == "admin":
    st.header("🛠 Admin Dashboard")
    t1, t2 = st.tabs(["Add Accounts", "System Clean-up"])
    with t1:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.subheader("Add Student")
            s_full_name = st.text_input("Student Full Name")
            s_cls = st.selectbox("Assign Class", CLASSES)
            if st.button("Create Student"):
                if s_full_name and s_full_name not in users.username.values:
                    users = pd.concat([users, pd.DataFrame([[s_full_name, hash_password("1234"), "student"]], columns=users.columns)], ignore_index=True)
                    students = pd.concat([students, pd.DataFrame([[s_full_name, s_cls]], columns=students.columns)], ignore_index=True)
                    save(users, USERS_FILE); save(students, STUDENTS_FILE)
                    st.success(f"Added {s_full_name}"); st.rerun()
        with c2:
            st.subheader("Add Teacher")
            t_name = st.text_input("Teacher Username")
            if st.button("Create Teacher"):
                if t_name and t_name not in users.username.values:
                    users = pd.concat([users, pd.DataFrame([[t_name, hash_password("1234"), "teacher"]], columns=users.columns)], ignore_index=True)
                    save(users, USERS_FILE)
                    st.success(f"Added {t_name}"); st.rerun()
        with c3:
            st.subheader("Add Parent")
            if not students.empty:
                target_student = st.selectbox("Select Child", students["student"].unique())
                p_username = f"{target_student}1"
                # Logic: Password is the first name of the child
                p_password_plain = target_student.split()[0] 
                
                st.info(f"User: **{p_username}**")
                st.info(f"Pass: **{p_password_plain}**")
                
                if st.button("Generate Parent Account"):
                    if p_username not in users.username.values:
                        users = pd.concat([users, pd.DataFrame([[p_username, hash_password(p_password_plain), "parent"]], columns=users.columns)], ignore_index=True)
                        save(users, USERS_FILE)
                        st.success(f"Account Active for {target_student}"); st.rerun()
                    else:
                        st.error("Account already exists.")
            else:
                st.warning("No students registered yet.")

    with t2:
        target_list = users[users.username != "admin"]["username"].tolist()
        if target_list:
            target = st.selectbox("Select User to Remove", target_list)
            if st.button("🔥 Delete User"):
                users = users[users.username != target]
                save(users, USERS_FILE); st.rerun()

# =========================
# TEACHER SECTION
# =========================
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
        tab_m, tab_a = st.tabs(["Subject Grading", "Attendance Entry"])
        
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
                            new_rows = [[r.Student, sel_cls, sel_term, subj, r.Marks] for _, r in res.iterrows()]
                            marks = pd.concat([marks, pd.DataFrame(new_rows, columns=marks.columns)], ignore_index=True)
                            save(marks, MARKS_FILE); st.rerun()
            else:
                indiv_data = [{"Subject": s, "Marks": (marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==s)]["marks"].values[0] if not marks[(marks.student==sel_student)&(marks.term==sel_term)&(marks.subject==s)].empty else 0)} for s in all_subs]
                res_indiv = st.data_editor(pd.DataFrame(indiv_data), key="indiv_editor")
                if st.button(f"Save Marks for {sel_student}"):
                    marks = marks[~((marks.student==sel_student)&(marks.term==sel_term))]
                    new_rows = [[sel_student, sel_cls, sel_term, r.Subject, r.Marks] for _, r in res_indiv.iterrows()]
                    marks = pd.concat([marks, pd.DataFrame(new_rows, columns=marks.columns)], ignore_index=True)
                    save(marks, MARKS_FILE); st.rerun()

        with tab_a:
            if sel_student == "-- All Students --":
                att_list = [attendance[(attendance.student==s)&(attendance.term==sel_term)]["days_present"].values[0] if not attendance[(attendance.student==s)&(attendance.term==sel_term)].empty else 0 for s in class_students]
                res_att = st.data_editor(pd.DataFrame({"Student": class_students, "Days Present": att_list}), key="bulk_att")
                if st.button("Save Attendance List"):
                    attendance = attendance[~((attendance.term==sel_term)&(attendance.student.isin(class_students)))]
                    new_rows = [[r.Student, sel_cls, sel_term, min(r['Days Present'], MAX_SCHOOL_DAYS)] for _, r in res_att.iterrows()]
                    attendance = pd.concat([attendance, pd.DataFrame(new_rows, columns=attendance.columns)], ignore_index=True)
                    save(attendance, ATTENDANCE_FILE); st.rerun()
            else:
                curr_att = attendance[(attendance.student==sel_student)&(attendance.term==sel_term)]["days_present"].values[0] if not attendance[(attendance.student==sel_student)&(attendance.term==sel_term)].empty else 0
                new_att = st.number_input(f"Days Present", 0, MAX_SCHOOL_DAYS, int(curr_att))
                if st.button(f"Update Attendance"):
                    attendance = attendance[~((attendance.student==sel_student)&(attendance.term==sel_term))]
                    attendance = pd.concat([attendance, pd.DataFrame([[sel_student, sel_cls, sel_term, new_att]], columns=attendance.columns)], ignore_index=True)
                    save(attendance, ATTENDANCE_FILE); st.rerun()

# =========================
# STUDENT & PARENT VIEW
# =========================
elif role in ["student", "parent"]:
    # Identify whose data to show
    target_student = user["username"][:-1] if role == "parent" else user["username"]
    
    st.header(f"📊 {'Parent Portal' if role == 'parent' else 'Student Dashboard'}")
    st.subheader(f"Academic Report for: {target_student}")
    
    m = marks[marks.student == target_student].copy()
    att_df = attendance[attendance.student == target_student].copy()
    
    if m.empty:
        st.info("Academic records are still being processed.")
    else:
        avg_score = m.marks.mean()
        current_grade, points = get_kcse_grade(avg_score)
        total_days = att_df.days_present.sum() if not att_df.empty else 0
        recorded_terms = len(att_df) if not att_df.empty else 0
        avg_att_pct = ((total_days / (recorded_terms * MAX_SCHOOL_DAYS)) * 100) if recorded_terms > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Current Mean Score", f"{round(avg_score, 1)}%")
        c2.metric("KCSE Grade", current_grade, f"{points} Points")
        c3.metric("Attendance Consistency", f"{round(avg_att_pct, 1)}%")
        
        st.divider()
        m['term_rank'] = m['term'].map(TERM_ORDER)
        m = m.sort_values('term_rank')
        
        col_charts_1, col_charts_2 = st.columns(2)
        with col_charts_1:
            st.subheader("📈 Performance Trend")
            st.line_chart(m.groupby("term", sort=False)["marks"].mean()) 

        with col_charts_2:
            st.subheader("🎯 Latest Marks")
            latest_term = m.iloc[-1]['term']
            st.bar_chart(m[m.term == latest_term].set_index("subject")["marks"])

        # AI Prediction Table
        st.divider()
        st.subheader("🤖 Zein AI: Performance Forecast")
        preds = []
        for s in m.subject.unique():
            df_s = m[m.subject == s].copy()
            df_s["t_id"] = df_s.term.map(TERM_INDEX)
            df_s = df_s.sort_values("t_id")
            
            p_val = zein_predict(df_s.marks.tolist(), df_s.t_id.tolist())
            p_grade, _ = get_kcse_grade(p_val)
            is_weak = p_val < df_s.marks.mean() or p_grade in ['D', 'D-', 'E']
            status = "⚠️ Action Required" if is_weak else "✅ On Track"
            
            preds.append({
                "Subject": s, 
                "Latest Mark": f"{df_s.marks.iloc[-1]}%",
                "AI Prediction": f"{round(p_val, 1)}%",
                "Projected Grade": p_grade,
                "Status": status
            })
        
        df_preds = pd.DataFrame(preds)

        def style_status(row):
            color = '#ff4b4b' if "Action" in row.Status else '#28a745'
            return [f'color: {color}'] * len(row)

        st.dataframe(df_preds.style.apply(style_status, axis=1), use_container_width=True)

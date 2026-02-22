import streamlit as st
import pandas as pd
import os
import hashlib
import numpy as np
from datetime import datetime

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School AI - Global", layout="wide")

SCHOOLS_FILE = "schools.csv"
USERS_FILE = "users.csv"
STUDENTS_FILE = "students.csv"
MARKS_FILE = "marks.csv"
ATTENDANCE_FILE = "attendance.csv"

CURRENT_YEAR = datetime.now().year
TERMS = ["Term 1", "Term 2", "Term 3"]

LEVEL_OPTIONS = {
    "Junior": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior": ["Grade 10", "Grade 11", "Grade 12"],
    "Both": ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
}

# =========================
# UTILITIES & AI ENGINE
# =========================
def hash_password(p):
    return hashlib.sha256(str(p).encode()).hexdigest()

def load_data(file, expected_cols, default_rows=None):
    if not os.path.exists(file):
        df = pd.DataFrame(default_rows or [], columns=expected_cols)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    for col in expected_cols:
        if col not in df.columns: df[col] = ""
    return df

def save(df, file):
    df.to_csv(file, index=False)

def predict_performance(marks_list, attendance_list):
    """Zein AI: Simple Linear Regression for performance forecasting"""
    if len(marks_list) < 2:
        return marks_list[-1] if marks_list else 0
    try:
        x = np.arange(len(marks_list))
        y = np.array(marks_list)
        coeffs = np.polyfit(x, y, 1)
        prediction = coeffs[0] * (len(marks_list)) + coeffs[1]
        
        # Adjust based on attendance trend
        if attendance_list and len(attendance_list) > 1:
            att_trend = attendance_list[-1] - np.mean(attendance_list)
            prediction += (att_trend * 0.1) 
            
        return max(0, min(100, prediction))
    except:
        return marks_list[-1]

# =========================
# DATA INITIALIZATION
# =========================
schools = load_data(SCHOOLS_FILE, ["school_name", "type", "status"])
users = load_data(USERS_FILE, ["username", "password", "role", "school", "phone"], 
                 [["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000"]])
students = load_data(STUDENTS_FILE, ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year"])
marks = load_data(MARKS_FILE, ["adm_no", "school", "year", "term", "subject", "marks"])
attendance = load_data(ATTENDANCE_FILE, ["adm_no", "school", "year", "term", "days_present"])

# =========================
# LOGIN & RECOVERY
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    t_login, t_forgot = st.tabs(["Login", "Forgot Password"])
    
    with t_login:
        u = st.text_input("Username / ADM / Phone")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            match = users[(users.username == str(u)) & (users.password == hash_password(p))]
            if not match.empty:
                u_dat = match.iloc[0].to_dict()
                sch_info = schools[schools.school_name == u_dat['school']]
                if not sch_info.empty and sch_info.iloc[0]['status'] == "Locked":
                    st.error("Account Suspended. Contact System Admin.")
                else:
                    st.session_state.user = u_dat
                    st.rerun()
            else: st.error("Invalid credentials.")

    with t_forgot:
        st.info("Security Question: Who is Zein?")
        ans = st.text_input("Answer", type="password")
        target_u = st.text_input("Username to Reset")
        new_pass = st.text_input("New Password", type="password")
        if st.button("Reset Password"):
            if ans.lower().replace(" ", "") == "zeiniszein":
                if target_u in users.username.values:
                    users.loc[users.username == target_u, 'password'] = hash_password(new_pass)
                    save(users, USERS_FILE)
                    st.success("Password reset successful!")
                else: st.error("User not found.")
            else: st.error("Wrong security answer.")
    st.stop()

# =========================
# APP SHELL
# =========================
user = st.session_state.user
role = user["role"]
my_school = user["school"]

if my_school != "SYSTEM":
    st.markdown(f"<h1 style='opacity: 0.04; position: fixed; top: 30%; left: 50%; transform: translateX(-50%); font-size: 130px; z-index: -1; text-align: center; width: 100%; pointer-events: none;'>{my_school}</h1>", unsafe_allow_html=True)

st.sidebar.title("Zein AI")
st.sidebar.write(f"Logged in: **{user['username']}**")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# SUPER ADMIN (ZEIN)
# =========================
if role == "superadmin":
    st.header("🌐 Master System Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Add School")
        s_name = st.text_input("School Name")
        s_type = st.selectbox("School Level", ["Junior", "Senior", "Both"])
        if st.button("Activate Institution"):
            if s_name and s_name not in schools.school_name.values:
                schools = pd.concat([schools, pd.DataFrame([[s_name, s_type, "Active"]], columns=schools.columns)], ignore_index=True)
                save(schools, SCHOOLS_FILE)
                users = pd.concat([users, pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000"]], columns=users.columns)], ignore_index=True)
                save(users, USERS_FILE)
                st.success(f"{s_name} is now live."); st.rerun()
    with c2:
        st.subheader("Current Institutions")
        st.dataframe(schools, use_container_width=True)
        target = st.selectbox("Select School", schools.school_name.unique())
        if st.button("Toggle Lock"):
            idx = schools[schools.school_name == target].index
            schools.at[idx[0], 'status'] = "Locked" if schools.at[idx[0], 'status'] == "Active" else "Active"
            save(schools, SCHOOLS_FILE); st.rerun()

# =========================
# SCHOOL ADMIN
# =========================
elif role == "admin":
    st.header(f"🏫 Management Dashboard: {my_school}")
    t1, t2, t3 = st.tabs(["Enrollment", "Staff Management", "End of Year"])
    sch_cfg = schools[schools.school_name == my_school].iloc[0]['type']
    
    with t1:
        with st.form("enroll"):
            c1, c2 = st.columns(2)
            adm = c1.text_input("ADM Number")
            kemis = c1.text_input("KEMIS Number")
            name = c2.text_input("Full Name")
            phone = c2.text_input("Parent Phone")
            cls = st.selectbox("Grade", LEVEL_OPTIONS[sch_cfg])
            if st.form_submit_button("Submit"):
                students = pd.concat([students, pd.DataFrame([[adm, kemis, name, cls, my_school, phone, CURRENT_YEAR]], columns=students.columns)], ignore_index=True)
                users = pd.concat([users, pd.DataFrame([
                    [phone, hash_password(phone), "parent", my_school, phone],
                    [adm, hash_password("1234"), "student", my_school, phone]
                ], columns=users.columns)], ignore_index=True).drop_duplicates('username')
                save(students, STUDENTS_FILE); save(users, USERS_FILE)
                st.success("Student added successfully.")

    with t2:
        st.subheader("Add Teacher")
        t_user = st.text_input("Username")
        t_pass = st.text_input("Password", type="password")
        if st.button("Create Teacher"):
            users = pd.concat([users, pd.DataFrame([[t_user, hash_password(t_pass), "teacher", my_school, "000"]], columns=users.columns)], ignore_index=True)
            save(users, USERS_FILE); st.success("Teacher account active.")

    with t3:
        st.subheader("Promotion System")
        p_from = st.selectbox("From Grade", LEVEL_OPTIONS[sch_cfg])
        p_to = st.selectbox("To Grade", ["Graduated"] + LEVEL_OPTIONS[sch_cfg])
        if st.button("Execute Promotion"):
            students.loc[(students.school == my_school) & (students['class'] == p_from), 'class'] = p_to
            save(students, STUDENTS_FILE); st.success("Batch promoted.")

# =========================
# TEACHER ROLE
# =========================
elif role == "teacher":
    st.header("📝 Classroom Data Entry")
    sch_cfg = schools[schools.school_name == my_school].iloc[0]['type']
    t_m, t_a = st.tabs(["Marks", "Attendance"])
    
    sel_cls = st.sidebar.selectbox("Grade", LEVEL_OPTIONS[sch_cfg])
    sel_term = st.sidebar.selectbox("Term", TERMS)
    cls_stds = students[(students.school == my_school) & (students['class'] == sel_cls)]
    
    with t_m:
        subj = st.text_input("Subject Name")
        if not cls_stds.empty and subj:
            df_m = pd.DataFrame({"ADM": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Marks": 0.0})
            edit_m = st.data_editor(df_m, use_container_width=True)
            if st.button("Save Marks"):
                new_m = [[r['ADM'], my_school, CURRENT_YEAR, sel_term, subj, r['Marks']] for _, r in edit_m.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_m, columns=marks.columns)], ignore_index=True)
                save(marks, MARKS_FILE); st.success("Saved.")

    with t_a:
        if not cls_stds.empty:
            df_a = pd.DataFrame({"ADM": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Days Present": 0})
            edit_a = st.data_editor(df_a, use_container_width=True)
            if st.button("Save Attendance"):
                new_a = [[r['ADM'], my_school, CURRENT_YEAR, sel_term, r['Days Present']] for _, r in edit_a.iterrows()]
                attendance = pd.concat([attendance, pd.DataFrame(new_a, columns=attendance.columns)], ignore_index=True)
                save(attendance, ATTENDANCE_FILE); st.success("Attendance Updated.")

# =========================
# PARENT / STUDENT VIEW
# =========================
elif role in ["parent", "student"]:
    st.header("📊 Performance Hub")
    my_stds = students[students.parent_phone == user['username']] if role == "parent" else students[students.adm_no == user['username']]
    
    if not my_stds.empty:
        sel_adm = st.selectbox("Student Profile", my_stds.adm_no.unique())
        std = my_stds[my_stds.adm_no == sel_adm].iloc[0]
        
        hist = marks[marks.adm_no == sel_adm]['year'].unique().tolist()
        if str(CURRENT_YEAR) not in [str(y) for y in hist]: hist.append(CURRENT_YEAR)
        sel_yr = st.sidebar.selectbox("Year Filter", sorted(hist, reverse=True))
        
        st.subheader(f"{std['name']} | ADM: {std['adm_no']} | KEMIS: {std['kemis_no']}")
        
        # Pull Data for Display & AI
        y_marks = marks[(marks.adm_no == sel_adm) & (marks.year == str(sel_yr))]
        y_att = attendance[(attendance.adm_no == sel_adm) & (attendance.year == str(sel_yr))]
        
        col_m, col_a = st.columns(2)
        
        with col_m:
            st.markdown("### 📚 Academic Marks")
            if not y_marks.empty:
                st.table(y_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='first').fillna("-"))
            else: st.info("No marks yet.")

        with col_a:
            st.markdown("### 📅 Attendance Record")
            if not y_att.empty:
                st.table(y_att.pivot_table(index='term', values='days_present', aggfunc='first').fillna(0))
            else: st.info("No attendance data.")

        # --- ZEIN AI ANALYTICS ---
        st.divider()
        st.markdown("### 🤖 Zein AI: Performance Forecast")
        if not y_marks.empty:
            all_subjects = y_marks['subject'].unique()
            forecasts = []
            for s in all_subjects:
                s_marks = y_marks[y_marks.subject == s].sort_values('term')['marks'].tolist()
                s_att = y_att.sort_values('term')['days_present'].tolist()
                
                pred = predict_performance(s_marks, s_att)
                trend = "📈 Improving" if pred > np.mean(s_marks) else "📉 Declining"
                
                forecasts.append({"Subject": s, "Current Avg": f"{round(np.mean(s_marks),1)}%", "AI Projected": f"{round(pred,1)}%", "Trend": trend})
            
            st.dataframe(pd.DataFrame(forecasts), use_container_width=True)
            st.caption("AI prediction is based on the correlation between current marks and attendance consistency.")
        else:
            st.warning("Insufficient data for AI analysis.")

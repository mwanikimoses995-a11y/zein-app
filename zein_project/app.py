import streamlit as st
import pandas as pd
import os
import hashlib
import io
from datetime import datetime

# =========================
# SAFETY IMPORT CHECK
# =========================
try:
    import plotly.express as px
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# =========================
# CONFIG & FILE PATHS
# =========================
st.set_page_config(page_title="Zein School AI - Global", layout="wide", page_icon="🎓")

FILES = {
    "schools": "schools.csv",
    "users": "users.csv",
    "students": "students.csv",
    "marks": "marks.csv"
}

COLS = {
    "schools": ["school_name", "type", "status"],
    "users": ["username", "password", "role", "school", "phone", "recovery_hint", "first_login", "assigned_subject"],
    "students": ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year", "status"],
    "marks": ["adm_no", "school", "year", "term", "subject", "marks"]
}

CBE_SUBJECTS = [
    "Mathematics", "English", "Kiswahili", "Integrated Science", "Health Education", 
    "Social Studies", "Pre-Technical Studies", "Business Studies", "Agriculture", 
    "Nutrition", "Life Skills Education", "Physical Education and Sports", 
    "Religious Education (CRE/IRE/HRE)", "Creative Arts and Philantropy", 
    "Computer Science", "Foreign Languages"
]

CURRENT_YEAR = str(datetime.now().year)
TERMS = ["Term 1", "Term 2", "Term 3"]
LEVEL_OPTIONS = {
    "Junior": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior": ["Grade 10", "Grade 11", "Grade 12"],
    "Both": ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
}

# =========================
# UTILITIES
# =========================
def hash_password(p):
    return hashlib.sha256(str(p).encode()).hexdigest()

def get_grade(score):
    try:
        score = float(score)
        if score >= 80: return "A (Exceeding Expectations)"
        if score >= 60: return "B (Meeting Expectations)"
        if score >= 40: return "C (Approaching Expectations)"
        return "D (Below Expectations)"
    except: return "N/A"

def load_data(key):
    file = FILES[key]
    expected = COLS[key]
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=expected)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file, dtype=str)
    if key == "marks" and not df.empty:
        df['marks'] = pd.to_numeric(df['marks'], errors='coerce')
    return df

def save(df, key):
    df.to_csv(FILES[key], index=False)

# Initial Data Load
schools = load_data("schools")
users = load_data("users")
students = load_data("students")
marks = load_data("marks")

# Create SuperAdmin if system is new
if "zein" not in users['username'].values:
    superadmin = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000", "founder", "False", "All"]], columns=COLS["users"])
    users = pd.concat([users, superadmin], ignore_index=True)
    save(users, "users")

# =========================
# LOGIN SYSTEM
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    tab_login, tab_forgot = st.tabs(["Sign In", "Forgot Password"])
    
    with tab_login:
        u_input = st.text_input("Username / ADM / Phone").strip()
        p_input = st.text_input("Password", type="password").strip()
        if st.button("Sign In", use_container_width=True):
            user_match = users[users.username == u_input]
            if not user_match.empty and user_match.iloc[0]['password'] == hash_password(p_input):
                st.session_state.user = user_match.iloc[0].to_dict()
                st.rerun()
            else: st.error("Invalid credentials.")

    with tab_forgot:
        rec_u = st.text_input("Username for Recovery").strip()
        if rec_u:
            user_row = users[users.username == rec_u]
            if not user_row.empty:
                st.info(f"**Hint:** {user_row.iloc[0]['recovery_hint']}")
            else: st.error("User not found.")
    st.stop()

logged_in_user = st.session_state.user

# MANDATORY: Set Password on First Login (For Admin & Teacher)
if str(logged_in_user.get("first_login")) == "True":
    st.warning("🔒 Security: You are using a temporary account. Please set your permanent password.")
    new_p = st.text_input("New Password", type="password")
    conf_p = st.text_input("Confirm New Password", type="password")
    if st.button("Activate Account"):
        if new_p == conf_p and len(new_p) >= 4:
            users.loc[users.username == logged_in_user['username'], ['password', 'first_login']] = [hash_password(new_p), "False"]
            save(users, "users")
            st.success("Password Updated! Please log in again.")
            st.session_state.clear(); st.rerun()
        else: st.error("Passwords must match and be 4+ characters.")
    st.stop()

# Dashboard Sidebar
role, my_school = logged_in_user["role"], str(logged_in_user["school"])
st.sidebar.title("Zein AI")
st.sidebar.write(f"User: **{logged_in_user['username']}**")
st.sidebar.write(f"Role: **{role.upper()}**")
if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# =========================
# SUPERADMIN
# =========================
if role == "superadmin":
    st.header("🌐 Global Master Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        s_name = st.text_input("School Name (Admin Username)").strip()
        s_lvl = st.selectbox("School Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if s_name and s_name not in schools['school_name'].values:
                new_sch = pd.DataFrame([[s_name, s_lvl, "Active"]], columns=COLS["schools"])
                schools = pd.concat([schools, new_sch], ignore_index=True)
                save(schools, "schools")
                new_u = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000", "Initial", "True", "All"]], columns=COLS["users"])
                users = pd.concat([users, new_u], ignore_index=True)
                save(users, "users")
                st.success(f"Activated. Temp Password: {s_name}")
            else: st.error("School already exists or name empty.")
    with c2: st.dataframe(schools)

# =========================
# ADMIN: ENROLL, STAFF, PROMOTE
# =========================
elif role == "admin":
    st.header(f"🏫 Admin Hub: {my_school}")
    t1, t2, t3, t4 = st.tabs(["Enrollment", "Bulk Upload", "Staff Management", "Promotion"])
    
    with t1:
        with st.form("enroll", clear_on_submit=True):
            col1, col2 = st.columns(2)
            adm, kemis, name = col1.text_input("ADM No"), col1.text_input("KEMIS No"), col1.text_input("Student Name")
            grade = col2.selectbox("Grade", LEVEL_OPTIONS.get(schools[schools.school_name==my_school].iloc[0]['type'], ["Grade 7"]))
            p_phone, hint = col2.text_input("Parent Phone"), col2.text_input("Recovery Hint")
            if st.form_submit_button("Enroll Individual"):
                if adm and name and p_phone:
                    new_std = pd.DataFrame([[adm, kemis, name, grade, my_school, p_phone, CURRENT_YEAR, "Active"]], columns=COLS["students"])
                    students = pd.concat([students, new_std], ignore_index=True)
                    save(students, "students")
                    u_data = pd.DataFrame([
                        [p_phone, hash_password(p_phone), "parent", my_school, p_phone, hint, "False", "None"],
                        [adm, hash_password("1234"), "student", my_school, p_phone, "1234", "False", "None"]
                    ], columns=COLS["users"])
                    users = pd.concat([users, u_data], ignore_index=True).drop_duplicates('username', keep='last')
                    save(users, "users"); st.success("Student and Parent accounts created.")

    with t2:
        st.subheader("Bulk Enrollment")
        template = pd.DataFrame(columns=["adm_no", "kemis_no", "name", "class", "parent_phone"])
        st.download_button("Download Template CSV", template.to_csv(index=False), "template.csv", "text/csv")
        up = st.file_uploader("Upload CSV", type="csv")
        if up and st.button("Process Bulk Upload"):
            df_up = pd.read_csv(up, dtype=str)
            df_up['school'], df_up['reg_year'], df_up['status'] = my_school, CURRENT_YEAR, "Active"
            students = pd.concat([students, df_up], ignore_index=True).drop_duplicates('adm_no', keep='last')
            save(students, "students")
            st.success(f"Enrolled {len(df_up)} students.")

    with t3:
        with st.form("teacher_reg"):
            t_user = st.text_input("Teacher Username")
            t_subj = st.selectbox("CBE Subject", CBE_SUBJECTS)
            if st.form_submit_button("Register Staff"):
                new_t = pd.DataFrame([[t_user, hash_password(t_user), "teacher", my_school, "000", "Staff", "True", t_subj]], columns=COLS["users"])
                users = pd.concat([users, new_t], ignore_index=True).drop_duplicates('username', keep='last')
                save(users, "users"); st.success(f"Teacher {t_user} registered. Their username is their temporary password.")

    with t4:
        st.warning("Annual Promotion moves students to the next grade.")
        if st.button("Run Promotion Now"):
            sch_type = schools[schools.school_name==my_school].iloc[0]['type']
            lvl_list = LEVEL_OPTIONS.get(sch_type, [])
            for i, r in students[students.school == my_school].iterrows():
                if r['status'] == "Active" and r['class'] in lvl_list:
                    idx = lvl_list.index(r['class'])
                    if idx + 1 < len(lvl_list): students.at[i, 'class'] = lvl_list[idx+1]
                    else: students.at[i, 'status'] = "Alumni"
            save(students, "students"); st.success("Promotion complete.")

# =========================
# TEACHER
# =========================
elif role == "teacher":
    assigned_subj = logged_in_user.get("assigned_subject", "Not Assigned")
    st.header(f"📝 {assigned_subj} Portal")
    
    t_tab1, t_tab2 = st.tabs(["Marks Entry", "Class Analytics"])
    
    lvl = schools[schools.school_name==my_school].iloc[0]['type']
    sel_g = st.sidebar.selectbox("Grade", LEVEL_OPTIONS.get(lvl, []))
    sel_t = st.sidebar.selectbox("Term", TERMS)
    
    with t_tab1:
        cur_stds = students[(students.school == my_school) & (students['class'] == sel_g) & (students.status == "Active")]
        if not cur_stds.empty:
            entry_df = pd.DataFrame({"adm_no": cur_stds.adm_no.values, "Name": cur_stds.name.values, "Score": 0.0})
            edited = st.data_editor(entry_df, use_container_width=True, hide_index=True)
            if st.button("Submit Marks"):
                new_marks = [[str(r['adm_no']), my_school, CURRENT_YEAR, sel_t, assigned_subj, r['Score']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_marks, columns=COLS["marks"])], ignore_index=True)
                marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                save(marks, "marks"); st.success("Marks synced successfully.")
        else: st.info("No active students found in this grade.")

    with t_tab2:
        if not HAS_PLOTLY:
            st.error("📉 Analytics Unavailable: Please run `pip install plotly`.")
        else:
            class_marks = marks[(marks.school == my_school) & (marks.subject == assigned_subj) & (marks.year == CURRENT_YEAR) & (marks.term == sel_t)]
            if not class_marks.empty:
                fig = px.bar(class_marks, x='adm_no', y='marks', title=f"{assigned_subj} Performance", color='marks', color_continuous_scale='RdYlGn')
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("No mark data available yet.")

# =========================
# STUDENT / PARENT
# =========================
elif role in ["parent", "student"]:
    st.header("📊 Performance Results")
    search_id = logged_in_user['username']
    my_stds = students[students.parent_phone == search_id] if role == 'parent' else students[students.adm_no == search_id]
    
    if not my_stds.empty:
        s_adm = st.selectbox("Select Profile", my_stds.adm_no.unique())
        info = my_stds[my_stds.adm_no == s_adm].iloc[0]
        st.subheader(f"{info['name']} | ADM: {info['adm_no']}")
        
        tab_c, tab_a = st.tabs(["Current Year", "Archives"])
        with tab_c:
            curr = marks[(marks.adm_no == str(s_adm)) & (marks.year == CURRENT_YEAR)]
            if not curr.empty:
                st.table(curr.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
                st.divider()
                cols = st.columns(3)
                for i, t in enumerate(TERMS):
                    t_data = curr[curr.term == t]
                    if not t_data.empty:
                        avg = t_data['marks'].mean()
                        cols[i].metric(f"{t} Average", f"{avg:.1f}%", get_grade(avg))
            else: st.info("No current results.")

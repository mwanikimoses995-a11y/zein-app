import streamlit as st
import pandas as pd
import os
import hashlib
from datetime import datetime

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
    "users": ["username", "password", "role", "school", "phone", "recovery_hint", "first_login"],
    "students": ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year", "status"],
    "marks": ["adm_no", "school", "year", "term", "subject", "marks"]
}

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

def load_data(key):
    file = FILES[key]
    expected = COLS[key]
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        df = pd.DataFrame(columns=expected)
        df.to_csv(file, index=False)
        return df
    df = pd.read_csv(file)
    for col in expected:
        if col not in df.columns: df[col] = ""
    return df

def save(df, key):
    df.to_csv(FILES[key], index=False)

# Initial Load
schools = load_data("schools")
users = load_data("users")
students = load_data("students")
marks = load_data("marks")

# Create Global Superadmin
if "zein" not in users['username'].values:
    superadmin = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000", "founder", "False"]], columns=COLS["users"])
    users = pd.concat([users, superadmin], ignore_index=True)
    save(users, "users")

# =========================
# LOGIN & PASSWORD SETUP
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    tab_login, tab_forgot = st.tabs(["Sign In", "Forgot Password"])
    
    with tab_login:
        u_input = st.text_input("Username").strip()
        p_input = st.text_input("Password", type="password").strip()
        
        if st.button("Sign In", use_container_width=True):
            user_match = users[users.username == u_input]
            if not user_match.empty:
                db_pass = user_match.iloc[0]['password']
                if db_pass == hash_password(p_input):
                    st.session_state.user = user_match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid credentials.")
            else: st.error("User not found.")

    with tab_forgot:
        rec_u = st.text_input("Username for Recovery").strip()
        if rec_u:
            user_row = users[users.username == rec_u]
            if not user_row.empty:
                st.info(f"**Hint:** {user_row.iloc[0]['recovery_hint']}")
            else: st.error("User not found.")
    st.stop()

# Force Password Reset on First Login
logged_in_user = st.session_state.user
if str(logged_in_user.get("first_login")) == "True":
    st.warning("🔒 Security: Set your permanent password.")
    new_p = st.text_input("New Password", type="password")
    conf_p = st.text_input("Confirm Password", type="password")
    if st.button("Activate Account"):
        if new_p == conf_p and len(new_p) > 3:
            users.loc[users.username == logged_in_user['username'], ['password', 'first_login']] = [hash_password(new_p), "False"]
            save(users, "users")
            st.success("Success! Please re-login.")
            st.session_state.clear()
            st.rerun()
        else: st.error("Invalid password match.")
    st.stop()

# Sidebar Setup
role = logged_in_user["role"]
my_school = str(logged_in_user["school"])
st.sidebar.title("Zein AI")
st.sidebar.info(f"User: {logged_in_user['username']}\nSchool: {my_school}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# ROLES LOGIC
# =========================

if role == "superadmin":
    st.header("🌐 Global Master Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        s_name = st.text_input("Institution Name (Admin Username)").strip()
        s_type = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if s_name and s_name not in schools['school_name'].values:
                schools = pd.concat([schools, pd.DataFrame([[s_name, s_type, "Active"]], columns=COLS["schools"])], ignore_index=True)
                save(schools, "schools")
                new_a = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000", "Initial", "True"]], columns=COLS["users"])
                users = pd.concat([users, new_a], ignore_index=True)
                save(users, "users")
                st.success(f"{s_name} active. Password is '{s_name}'")
    with c2: st.dataframe(schools)

elif role == "admin":
    st.header(f"🏫 Admin Hub: {my_school}")
    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    t1, t2, t3 = st.tabs(["Enrollment", "Staff", "Promotion System"])

    with t1:
        with st.form("enroll", clear_on_submit=True):
            col1, col2 = st.columns(2)
            adm = col1.text_input("ADM Number")
            kemis = col1.text_input("KEMIS Number")
            name = col1.text_input("Full Name")
            grade = col2.selectbox("Grade", LEVEL_OPTIONS.get(sch_type, ["Grade 7"]))
            p_phone = col2.text_input("Parent Phone")
            p_hint = col2.text_input("Recovery Hint")
            if st.form_submit_button("Register Student"):
                if all([adm, kemis, name, p_phone]):
                    s_data = pd.DataFrame([[adm, kemis, name, grade, my_school, p_phone, CURRENT_YEAR, "Active"]], columns=COLS["students"])
                    students = pd.concat([students, s_data], ignore_index=True)
                    save(students, "students")
                    u_data = pd.DataFrame([
                        [p_phone, hash_password(p_phone), "parent", my_school, p_phone, p_hint, "False"],
                        [adm, hash_password("1234"), "student", my_school, p_phone, "1234", "False"]
                    ], columns=COLS["users"])
                    users = pd.concat([users, u_data], ignore_index=True).drop_duplicates('username', keep='last')
                    save(users, "users")
                    st.success("Accounts Created.")

    with t3:
        st.subheader("End of Year Promotion")
        st.warning("This will advance all students to the next grade level.")
        if st.button("Promote All Students"):
            for i, row in students[students.school == my_school].iterrows():
                current_grade = row['class']
                all_grades = LEVEL_OPTIONS.get(sch_type, [])
                if current_grade in all_grades:
                    idx = all_grades.index(current_grade)
                    if idx + 1 < len(all_grades):
                        students.at[i, 'class'] = all_grades[idx+1]
                    else:
                        students.at[i, 'status'] = "Alumni"
            save(students, "students")
            st.success("Promotion Completed!")

elif role == "teacher":
    st.header("📝 Academic Entry")
    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    sel_cls = st.sidebar.selectbox("Grade", LEVEL_OPTIONS.get(sch_type, []))
    sel_term = st.sidebar.selectbox("Term", TERMS)
    
    active_stds = students[(students.school == my_school) & (students['class'] == sel_cls) & (students.status == "Active")]
    
    if not active_stds.empty:
        subj = st.text_input("Subject").strip()
        if subj:
            df_entry = pd.DataFrame({"adm_no": active_stds.adm_no.values, "Name": active_stds.name.values, "Marks": 0.0})
            edited = st.data_editor(df_entry, use_container_width=True, hide_index=True)
            if st.button("Save Grades"):
                new_m = [[str(r['adm_no']), my_school, CURRENT_YEAR, sel_term, subj, r['Marks']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(new_m, columns=COLS["marks"])], ignore_index=True)
                marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                save(marks, "marks"); st.success("Grades recorded.")
    else: st.info("No active students in this grade.")

elif role in ["parent", "student"]:
    st.header("📊 Results Center")
    search = logged_in_user['username']
    my_stds = students[students.parent_phone == search] if role == 'parent' else students[students.adm_no == search]
    
    if not my_stds.empty:
        sel_adm = st.selectbox("Select Student", my_stds.adm_no.unique())
        std_info = my_stds[my_stds.adm_no == sel_adm].iloc[0]
        
        st.subheader(f"{std_info['name']} ({std_info['class']})")
        
        tab_current, tab_history = st.tabs(["Current Year Results", "Past Years Archive"])
        
        with tab_current:
            c_marks = marks[(marks.adm_no == str(sel_adm)) & (marks.year == CURRENT_YEAR)]
            if not c_marks.empty:
                st.table(c_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
            else: st.warning("No marks for this year.")
            
        with tab_history:
            h_marks = marks[(marks.adm_no == str(sel_adm)) & (marks.year != CURRENT_YEAR)]
            if not h_marks.empty:
                years = sorted(h_marks.year.unique(), reverse=True)
                sel_year = st.selectbox("Select Past Year", years)
                y_data = h_marks[h_marks.year == sel_year]
                st.dataframe(y_data.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
            else: st.info("No historical data available.")

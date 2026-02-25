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
# UTILITIES & ANALYTICS
# =========================
def hash_password(p):
    return hashlib.sha256(str(p).encode()).hexdigest()

def get_grade(score):
    if score >= 80: return "A"
    if score >= 70: return "B"
    if score >= 60: return "C"
    if score >= 50: return "D"
    return "E"

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
                st.info(f"**Your Hint:** {user_row.iloc[0]['recovery_hint']}")
            else: st.error("User not found.")
    st.stop()

# Force Password Update for Admins
logged_in_user = st.session_state.user
if str(logged_in_user.get("first_login")) == "True":
    st.warning("🔒 First Login: Set your permanent password.")
    new_p = st.text_input("New Password", type="password")
    if st.button("Confirm Password"):
        users.loc[users.username == logged_in_user['username'], ['password', 'first_login']] = [hash_password(new_p), "False"]
        save(users, "users")
        st.success("Updated! Logging out..."); st.session_state.clear(); st.rerun()
    st.stop()

# Layout
role = logged_in_user["role"]
my_school = str(logged_in_user["school"])
st.sidebar.title("Zein AI")
st.sidebar.write(f"Logged: **{logged_in_user['username']}**")
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
            if s_name:
                schools = pd.concat([schools, pd.DataFrame([[s_name, s_lvl, "Active"]], columns=COLS["schools"])], ignore_index=True)
                save(schools, "schools")
                new_u = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000", "Admin", "True"]], columns=COLS["users"])
                users = pd.concat([users, new_u], ignore_index=True)
                save(users, "users")
                st.success(f"Activated. Temp Pass: {s_name}")
    with c2: st.dataframe(schools)

# =========================
# ADMIN: ENROLL & PROMOTE
# =========================
elif role == "admin":
    st.header(f"🏫 Admin Hub: {my_school}")
    t1, t2, t3 = st.tabs(["Enrollment", "Staff Management", "Promotion System"])
    
    with t1:
        with st.form("enroll", clear_on_submit=True):
            col1, col2 = st.columns(2)
            adm = col1.text_input("Admission Number")
            kemis = col1.text_input("KEMIS Number")
            name = col1.text_input("Student Name")
            grade = col2.selectbox("Grade", LEVEL_OPTIONS.get(schools[schools.school_name==my_school].iloc[0]['type'], ["Grade 7"]))
            p_phone = col2.text_input("Parent Phone (Login)")
            hint = col2.text_input("Recovery Hint")
            if st.form_submit_button("Complete Registration"):
                students = pd.concat([students, pd.DataFrame([[adm, kemis, name, grade, my_school, p_phone, CURRENT_YEAR, "Active"]], columns=COLS["students"])], ignore_index=True)
                save(students, "students")
                u_data = pd.DataFrame([
                    [p_phone, hash_password(p_phone), "parent", my_school, p_phone, hint, "False"],
                    [adm, hash_password("1234"), "student", my_school, p_phone, "1234", "False"]
                ], columns=COLS["users"])
                users = pd.concat([users, u_data], ignore_index=True).drop_duplicates('username', keep='last')
                save(users, "users"); st.success("Accounts Synchronized.")

    with t3:
        st.warning("⚠️ PROMOTION SYSTEM: This advances all active students to the next level.")
        if st.button("Run End of Year Promotion"):
            sch_lvl = schools[schools.school_name==my_school].iloc[0]['type']
            lvl_list = LEVEL_OPTIONS.get(sch_lvl, [])
            for i, r in students[students.school == my_school].iterrows():
                if r['status'] == "Active":
                    try:
                        idx = lvl_list.index(r['class'])
                        if idx + 1 < len(lvl_list): students.at[i, 'class'] = lvl_list[idx+1]
                        else: students.at[i, 'status'] = "Alumni"
                    except: pass
            save(students, "students"); st.success("Promotion sequence completed.")

# =========================
# TEACHER
# =========================
elif role == "teacher":
    st.header("📝 Marks Management")
    lvl = schools[schools.school_name==my_school].iloc[0]['type']
    sel_g = st.sidebar.selectbox("Grade", LEVEL_OPTIONS.get(lvl, []))
    sel_t = st.sidebar.selectbox("Term", TERMS)
    
    cl_stds = students[(students.school == my_school) & (students['class'] == sel_g) & (students.status == "Active")]
    if not cl_stds.empty:
        subj = st.text_input("Enter Subject Name").strip()
        if subj:
            entry = pd.DataFrame({"adm_no": cl_stds.adm_no.values, "Name": cl_stds.name.values, "Score": 0.0})
            edited = st.data_editor(entry, use_container_width=True, hide_index=True)
            if st.button("Finalize Grades"):
                rows = [[str(r['adm_no']), my_school, CURRENT_YEAR, sel_t, subj, r['Score']] for _, r in edited.iterrows()]
                marks = pd.concat([marks, pd.DataFrame(rows, columns=COLS["marks"])], ignore_index=True)
                marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                save(marks, "marks"); st.success("Data Uploaded.")
    else: st.info("No active students found.")

# =========================
# STUDENT / PARENT (RESULTS & ARCHIVE)
# =========================
elif role in ["parent", "student"]:
    st.header("📊 Performance Analytics")
    search = logged_in_user['username']
    my_stds = students[students.parent_phone == search] if role == 'parent' else students[students.adm_no == search]
    
    if not my_stds.empty:
        s_adm = st.selectbox("Select Profile", my_stds.adm_no.unique())
        info = my_stds[my_stds.adm_no == s_adm].iloc[0]
        st.subheader(f"{info['name']} | ADM: {info['adm_no']} | KEMIS: {info['kemis_no']}")
        
        tab1, tab2 = st.tabs(["Current Progress", "Archives (Past Years)"])
        
        with tab1:
            y_marks = marks[(marks.adm_no == str(s_adm)) & (marks.year == CURRENT_YEAR)]
            if not y_marks.empty:
                # Table
                pivot = y_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last')
                st.table(pivot.fillna("-"))
                
                # --- SUMMARY CARD ---
                st.divider()
                st.subheader("🏁 Term Summary (Mean Scores)")
                summary_cols = st.columns(3)
                for i, term in enumerate(TERMS):
                    t_data = y_marks[y_marks.term == term]
                    if not t_data.empty:
                        mean = t_data['marks'].mean()
                        summary_cols[i].metric(f"{term} Mean", f"{mean:.2f}%", f"Grade: {get_grade(mean)}")
            else: st.warning("No data for the current academic year.")

        with tab2:
            h_marks = marks[(marks.adm_no == str(s_adm)) & (marks.year != CURRENT_YEAR)]
            if not h_marks.empty:
                sel_y = st.selectbox("Choose Past Year", sorted(h_marks.year.unique(), reverse=True))
                hist = h_marks[h_marks.year == sel_y]
                st.dataframe(hist.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-"))
                st.info(f"Summary for {sel_y}: Mean Score {hist['marks'].mean():.2f}%")
            else: st.info("No historical data found in the archive.")
    else: st.error("Account not linked to any student profile.")

import streamlit as st
import pandas as pd
import os
import hashlib
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
st.set_page_config(page_title="Zein School AI", layout="wide", page_icon="🎓")

FILES = ["schools.csv", "users.csv", "students.csv", "marks.csv"]
COLS = {
    "schools": ["school_name", "type", "status"],
    "users": ["username", "password", "role", "school", "phone", "recovery_hint", "first_login", "assigned_subject"],
    "students": ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year", "status"],
    "marks": ["adm_no", "school", "year", "term", "subject", "marks"]
}

CBE_SUBJECTS = sorted([
    "Mathematics", "English", "Kiswahili", "Integrated Science", "Health Education", 
    "Social Studies", "Pre-Technical Studies", "Business Studies", "Agriculture", 
    "Nutrition", "Life Skills Education", "Physical Education and Sports", 
    "Religious Education (CRE/IRE/HRE)", "Creative Arts and Philantropy", 
    "Computer Science", "Foreign Languages"
])

CURRENT_YEAR = str(datetime.now().year)
TERMS = ["Term 1", "Term 2", "Term 3"]
LEVEL_OPTIONS = {
    "Junior": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior": ["Grade 10", "Grade 11", "Grade 12"],
    "Both": ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
}

# =========================
# CORE UTILITIES
# =========================
def hash_password(p):
    return hashlib.sha256(str(p).encode()).hexdigest()

def get_grade(score):
    try:
        s = float(score)
        if s >= 80: return "Exceeding Expectations (A)"
        if s >= 60: return "Meeting Expectations (B)"
        if s >= 40: return "Approaching Expectations (C)"
        return "Below Expectations (D)"
    except: return "N/A"

def load_data():
    data = {}
    for key, file in zip(COLS.keys(), FILES):
        if not os.path.exists(file) or os.stat(file).st_size == 0:
            df = pd.DataFrame(columns=COLS[key])
            df.to_csv(file, index=False)
            data[key] = df
        else:
            # dtype=str is vital to prevent ADM 001 becoming 1
            data[key] = pd.read_csv(file, dtype=str)
            if key == "marks":
                data[key]['marks'] = pd.to_numeric(data[key]['marks'], errors='coerce')
    return data

def save_data(df, key):
    file = FILES[list(COLS.keys()).index(key)]
    df.to_csv(file, index=False)

# Initialize
db = load_data()

# Superadmin Bootstrapping
if "zein" not in db['users']['username'].values:
    sa = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000", "Founder", "False", "All"]], columns=COLS["users"])
    db['users'] = pd.concat([db['users'], sa], ignore_index=True)
    save_data(db['users'], "users")

# =========================
# AUTHENTICATION
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    t1, t2 = st.tabs(["Sign In", "Recovery"])
    with t1:
        u = st.text_input("ID / Username").strip()
        p = st.text_input("Password", type="password").strip()
        if st.button("Login", use_container_width=True):
            user_row = db['users'][db['users'].username == u]
            if not user_row.empty and user_row.iloc[0]['password'] == hash_password(p):
                st.session_state.user = user_row.iloc[0].to_dict()
                st.rerun()
            else: st.error("Incorrect username or password.")
    st.stop()

user = st.session_state.user

# First Login Check
if str(user.get("first_login")) == "True":
    st.info("🔒 Security: Set a new password to activate your account.")
    new_p = st.text_input("New Password", type="password")
    if st.button("Update Password"):
        if len(new_p) >= 4:
            db['users'].loc[db['users'].username == user['username'], ['password', 'first_login']] = [hash_password(new_p), "False"]
            save_data(db['users'], "users")
            st.success("Updated! Please login again.")
            st.session_state.clear(); st.rerun()
        else: st.error("Password too short.")
    st.stop()

# Sidebar
st.sidebar.title("Zein AI")
st.sidebar.write(f"**{user['username']}** ({user['role'].upper()})")
if st.sidebar.button("Logout"):
    st.session_state.clear(); st.rerun()

# =========================
# DASHBOARD LOGIC
# =========================
role, my_school = user['role'], user['school']

if role == "superadmin":
    st.header("🌐 Global Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        name = st.text_input("School Name")
        lvl = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Create School"):
            if name and name not in db['schools'].school_name.values:
                new_sch = pd.DataFrame([[name, lvl, "Active"]], columns=COLS["schools"])
                db['schools'] = pd.concat([db['schools'], new_sch], ignore_index=True)
                save_data(db['schools'], "schools")
                # Create Admin Account
                new_adm = pd.DataFrame([[name, hash_password(name), "admin", name, "000", "Init", "True", "All"]], columns=COLS["users"])
                db['users'] = pd.concat([db['users'], new_adm], ignore_index=True)
                save_data(db['users'], "users")
                st.success("School Online!")
    with c2: st.dataframe(db['schools'])

elif role == "admin":
    st.header(f"🏫 Admin: {my_school}")
    tabs = st.tabs(["Enroll", "Bulk", "Staff", "Promote", "Search"])
    
    with tabs[0]: # Individual Enroll
        with st.form("indiv"):
            c1, c2 = st.columns(2)
            adm = c1.text_input("ADM No")
            name = c1.text_input("Full Name")
            phone = c2.text_input("Parent Phone")
            grade = c2.selectbox("Grade", LEVEL_OPTIONS.get(db['schools'][db['schools'].school_name==my_school].iloc[0]['type'], ["Grade 7"]))
            if st.form_submit_button("Enroll"):
                if adm and phone:
                    # Save Student
                    new_s = pd.DataFrame([[adm, "N/A", name, grade, my_school, phone, CURRENT_YEAR, "Active"]], columns=COLS["students"])
                    db['students'] = pd.concat([db['students'], new_s], ignore_index=True)
                    save_data(db['students'], "students")
                    # Create Accounts
                    u_std = [adm, hash_password("1234"), "student", my_school, phone, "1234", "False", "None"]
                    u_par = [phone, hash_password(phone), "parent", my_school, phone, "Phone", "False", "None"]
                    accs = pd.DataFrame([u_std, u_par], columns=COLS["users"])
                    db['users'] = pd.concat([db['users'], accs], ignore_index=True).drop_duplicates('username', keep='last')
                    save_data(db['users'], "users")
                    st.success("Accounts Created (Student Pass: 1234)")

    with tabs[1]: # Bulk
        up = st.file_uploader("Upload CSV (adm_no, name, class, parent_phone)", type="csv")
        if up:
            df_up = pd.read_csv(up, dtype=str)
            if st.button("Import All"):
                df_up['school'], df_up['reg_year'], df_up['status'] = my_school, CURRENT_YEAR, "Active"
                db['students'] = pd.concat([db['students'], df_up], ignore_index=True).drop_duplicates('adm_no', keep='last')
                save_data(db['students'], "students")
                st.success("Bulk Enrollment Complete")

    with tabs[4]: # Search
        query = st.text_input("Search Student Name/ADM")
        if query:
            res = db['students'][(db['students'].school == my_school) & 
                                (db['students'].name.str.contains(query, case=False) | (db['students'].adm_no == query))]
            st.table(res)

elif role == "teacher":
    subj = user.get("assigned_subject", "Unassigned")
    st.header(f"📝 Teacher Portal: {subj}")
    
    t1, t2 = st.tabs(["Marks Entry", "Analytics"])
    
    # Sidebar selectors for context
    sch_lvl = db['schools'][db['schools'].school_name==my_school].iloc[0]['type']
    sel_g = st.sidebar.selectbox("Class", LEVEL_OPTIONS.get(sch_lvl, []))
    sel_t = st.sidebar.selectbox("Term", TERMS)

    with t1:
        stds = db['students'][(db['students'].school == my_school) & (db['students']['class'] == sel_g) & (db['students'].status == "Active")]
        if not stds.empty:
            # Prepare entry grid
            entry = pd.DataFrame({"adm_no": stds.adm_no.values, "Name": stds.name.values, "Score": 0.0})
            edited = st.data_editor(entry, use_container_width=True, hide_index=True)
            if st.button("Save Marks"):
                rows = []
                for _, r in edited.iterrows():
                    rows.append([str(r['adm_no']), my_school, CURRENT_YEAR, sel_t, subj, r['Score']])
                new_m = pd.DataFrame(rows, columns=COLS["marks"])
                db['marks'] = pd.concat([db['marks'], new_m], ignore_index=True).drop_duplicates(['adm_no', 'year', 'term', 'subject'], keep='last')
                save_data(db['marks'], "marks")
                st.success("Marks Updated.")
        else: st.warning("No students found in this grade.")

    with t2:
        if not HAS_PLOTLY:
            st.error("Please run 'pip install plotly' to view charts.")
        else:
            m_data = db['marks'][(db['marks'].school == my_school) & (db['marks'].subject == subj) & (db['marks'].term == sel_t)]
            if not m_data.empty:
                fig = px.bar(m_data, x='adm_no', y='marks', color='marks', title=f"Performance: {sel_g} - {subj}")
                st.plotly_chart(fig, use_container_width=True)
            else: st.info("No data for chart.")

elif role in ["parent", "student"]:
    st.header("📊 Results Center")
    search_key = user['username']
    my_kids = db['students'][db['students'].parent_phone == search_key] if role == 'parent' else db['students'][db['students'].adm_no == search_key]
    
    if not my_kids.empty:
        target = st.selectbox("Select Student", my_kids.adm_no.unique())
        kid_info = my_kids[my_kids.adm_no == target].iloc[0]
        st.subheader(f"{kid_info['name']} | {kid_info['class']}")
        
        res = db['marks'][(db['marks'].adm_no == str(target)) & (db['marks'].year == CURRENT_YEAR)]
        if not res.empty:
            # Pivot correctly handles missing subjects/terms
            report = res.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-")
            st.table(report)
            
            # Summary Metrics
            cols = st.columns(3)
            for i, t in enumerate(TERMS):
                term_marks = res[res.term == t]['marks']
                if not term_marks.empty:
                    avg = term_marks.mean()
                    cols[i].metric(f"{t} Avg", f"{avg:.1f}%", get_grade(avg))
        else: st.info("No marks recorded yet for this year.")

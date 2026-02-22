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

# CBC Structure (Junior & Senior)
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

# =========================
# DATA INITIALIZATION
# =========================
schools = load_data(SCHOOLS_FILE, ["school_name", "type", "status"])
# Initializing Superadmin with requested credentials
users = load_data(USERS_FILE, ["username", "password", "role", "school", "phone"], 
                 [["zein", hash_password("zein2026"), "superadmin", "SYSTEM", "000"]])
students = load_data(STUDENTS_FILE, ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year"])
marks = load_data(MARKS_FILE, ["adm_no", "school", "year", "term", "subject", "marks"])

# =========================
# LOGIN & SECURITY
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    
    tab_login, tab_forgot = st.tabs(["Login", "Forgot Password"])
    
    with tab_login:
        u = st.text_input("Username / ADM / Parent Phone")
        p = st.text_input("Password", type="password")
        if st.button("Sign In"):
            match = users[(users.username == str(u)) & (users.password == hash_password(p))]
            if not match.empty:
                u_dat = match.iloc[0].to_dict()
                sch_stat = schools[schools.school_name == u_dat['school']]
                if not sch_stat.empty and sch_stat.iloc[0]['status'] == "Locked":
                    st.error("Access Denied: This school account has been suspended.")
                else:
                    st.session_state.user = u_dat
                    st.rerun()
            else:
                st.error("Invalid credentials")

    with tab_forgot:
        st.subheader("Account Recovery")
        st.info("Security Question: Who is Zein?")
        ans = st.text_input("Answer", type="password")
        target_user = st.text_input("Username to Reset")
        new_p = st.text_input("New Password", type="password")
        
        if st.button("Reset Password"):
            if ans.lower().replace(" ", "") == "zeiniszein":
                if target_user in users.username.values:
                    users.loc[users.username == target_user, 'password'] = hash_password(new_p)
                    save(users, USERS_FILE)
                    st.success("Password updated successfully! Please login.")
                else:
                    st.error("User not found.")
            else:
                st.error("Incorrect security answer.")
    st.stop()

# =========================
# DASHBOARD LOGIC
# =========================
user = st.session_state.user
role = user["role"]
my_school = user["school"]

# Background School Watermark
if my_school != "SYSTEM":
    st.markdown(f"""<h1 style='opacity: 0.05; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); font-size: 150px; z-index: -1; pointer-events: none;'>{my_school}</h1>""", unsafe_allow_html=True)

st.sidebar.title("Zein AI")
st.sidebar.info(f"Institution: {my_school}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# --- SUPERADMIN VIEW ---
if role == "superadmin":
    st.header("🌐 Global Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("Add New Institution")
        n_sch = st.text_input("School Name")
        n_type = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Register School"):
            if n_sch and n_sch not in schools.school_name.values:
                # Create School
                new_s = pd.DataFrame([[n_sch, n_type, "Active"]], columns=schools.columns)
                schools = pd.concat([schools, new_s], ignore_index=True)
                save(schools, SCHOOLS_FILE)
                # Create Admin (User/Pass = School Name)
                new_a = pd.DataFrame([[n_sch, hash_password(n_sch), "admin", n_sch, "000"]], columns=users.columns)
                users = pd.concat([users, new_a], ignore_index=True)
                save(users, USERS_FILE)
                st.success(f"{n_sch} Registered!")
                st.rerun()
    with c2:
        st.subheader("Manage Schools")
        st.dataframe(schools, use_container_width=True)
        sel_s = st.selectbox("Target School", schools.school_name.unique())
        if st.button("Lock/Unlock School"):
            idx = schools[schools.school_name == sel_s].index
            schools.at[idx[0], 'status'] = "Locked" if schools.at[idx[0], 'status'] == "Active" else "Active"
            save(schools, SCHOOLS_FILE)
            st.rerun()

# --- SCHOOL ADMIN VIEW ---
elif role == "admin":
    st.header(f"🏫 Admin: {my_school}")
    t1, t2 = st.tabs(["Enrollment", "Year-End Promotion"])
    
    with t1:
        with st.form("enroll"):
            st.subheader("Student Registration")
            c1, c2 = st.columns(2)
            adm = c1.text_input("Admission No")
            kemis = c1.text_input("KEMIS No")
            name = c2.text_input("Full Name")
            phone = c2.text_input("Parent Phone")
            
            sch_cfg = schools[schools.school_name == my_school].iloc[0]['type']
            cls = st.selectbox("Class", LEVEL_OPTIONS[sch_cfg])
            
            if st.form_submit_button("Register Student"):
                if adm and phone:
                    new_st = pd.DataFrame([[adm, kemis, name, cls, my_school, phone, CURRENT_YEAR]], columns=students.columns)
                    students = pd.concat([students, new_st], ignore_index=True)
                    save(students, STUDENTS_FILE)
                    
                    # Parent User (Phone) & Student User (ADM)
                    p_user = [phone, hash_password(phone), "parent", my_school, phone]
                    s_user = [adm, hash_password("1234"), "student", my_school, phone]
                    users = pd.concat([users, pd.DataFrame([p_user, s_user], columns=users.columns)], ignore_index=True).drop_duplicates('username')
                    save(users, USERS_FILE)
                    st.success("Registration Successful")

    with t2:
        st.subheader("Academic Year Transition")
        p_from = st.selectbox("From Grade", LEVEL_OPTIONS[sch_cfg])
        p_to = st.selectbox("To Grade", ["Graduated"] + LEVEL_OPTIONS[sch_cfg])
        if st.button("Bulk Promote Students"):
            students.loc[(students.school == my_school) & (students['class'] == p_from), 'class'] = p_to
            save(students, STUDENTS_FILE)
            st.success(f"Promotion successful for {p_from}")

# --- PARENT/STUDENT VIEW ---
elif role in ["parent", "student"]:
    st.header("📊 Student Report Card")
    my_data = students[(students.parent_phone == user['username'])] if role == "parent" else students[(students.adm_no == user['username'])]
    
    if not my_data.empty:
        sel_adm = st.selectbox("Select Student", my_data.adm_no.unique())
        std = my_data[my_data.adm_no == sel_adm].iloc[0]
        
        # Pull Historical Years
        available_years = marks[marks.adm_no == sel_adm]['year'].unique().tolist()
        if str(CURRENT_YEAR) not in [str(y) for y in available_years]: available_years.append(CURRENT_YEAR)
        sel_yr = st.sidebar.selectbox("Filter Year", sorted(available_years, reverse=True))
        
        st.write(f"**Name:** {std['name']} | **Class:** {std['class']} | **ADM:** {std['adm_no']}")
        
        y_marks = marks[(marks.adm_no == sel_adm) & (marks.year == str(sel_yr))]
        if not y_marks.empty:
            report = y_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='first').fillna("-")
            st.table(report)
        else:
            st.info(f"No academic data found for the year {sel_yr}.")

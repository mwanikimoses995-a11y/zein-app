import streamlit as st
import pandas as pd
import os
import hashlib
import io
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
    "users": ["username", "password", "role", "school", "phone", "recovery_hint"],
    "students": ["adm_no", "name", "class", "school", "parent_phone", "reg_year"],
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

# Global Superadmin Creation
if "zein" not in users['username'].values:
    superadmin = pd.DataFrame([["zein", hash_password("mionmion"), "superadmin", "SYSTEM", "000", "founder"]], columns=COLS["users"])
    users = pd.concat([users, superadmin], ignore_index=True)
    save(users, "users")

# =========================
# LOGIN & RECOVERY SYSTEM
# =========================
if "user" not in st.session_state:
    st.title("🛡️ Zein School AI Portal")
    tab_login, tab_forgot = st.tabs(["Sign In", "Forgot Password"])
    
    with tab_login:
        with st.container(border=True):
            u = st.text_input("Username / Parent Phone").strip()
            p = st.text_input("Password", type="password").strip()
            if st.button("Sign In", use_container_width=True):
                match = users[(users.username == u) & (users.password == hash_password(p))]
                if not match.empty:
                    st.session_state.user = match.iloc[0].to_dict()
                    st.rerun()
                else: st.error("Invalid credentials.")
    
    with tab_forgot:
        st.info("Enter your username to see your recovery hint.")
        rec_u = st.text_input("Username for Recovery").strip()
        if rec_u:
            user_row = users[users.username == rec_u]
            if not user_row.empty:
                st.write(f"**Your Security Hint:** {user_row.iloc[0]['recovery_hint']}")
                st.caption("Contact your School Admin to reset if you still can't log in.")
            else: st.error("User not found.")
    st.stop()

# Session Globals
logged_in_user = st.session_state.user
role = logged_in_user["role"]
my_school = str(logged_in_user["school"])

st.sidebar.title("Zein AI")
st.sidebar.info(f"User: {logged_in_user['username']}\nRole: {role.upper()}")
if st.sidebar.button("Logout"):
    st.session_state.clear()
    st.rerun()

# =========================
# SUPERADMIN: SYSTEM CONTROL
# =========================
if role == "superadmin":
    st.header("🌐 Global Master Controller")
    c1, c2 = st.columns([1, 2])
    with c1:
        s_name = st.text_input("Institution Name")
        s_type = st.selectbox("Level", ["Junior", "Senior", "Both"])
        if st.button("Activate School"):
            if s_name and s_name not in schools['school_name'].values:
                new_sch = pd.DataFrame([[s_name, s_type, "Active"]], columns=COLS["schools"])
                schools = pd.concat([schools, new_sch], ignore_index=True)
                save(schools, "schools")
                # Create Admin for that school
                new_a = pd.DataFrame([[s_name, hash_password(s_name), "admin", s_name, "000", "school_name"]], columns=COLS["users"])
                users = pd.concat([users, new_a], ignore_index=True)
                save(users, "users")
                st.success(f"{s_name} Activated!"); st.rerun()
    with c2: st.dataframe(schools, use_container_width=True)

# =========================
# ADMIN: ENROLLMENT & STAFF
# =========================
elif role == "admin":
    sch_type = schools[schools.school_name == my_school].iloc[0]['type'] if not schools[schools.school_name == my_school].empty else "Both"
    st.header(f"🏫 Admin Dashboard: {my_school}")
    t1, t2 = st.tabs(["Student Enrollment", "Staff Management"])
    
    with t1:
        st.subheader("New Student & Parent Registration")
        with st.form("enroll", clear_on_submit=True):
            col_a, col_b = st.columns(2)
            adm = col_a.text_input("Student ADM Number")
            name = col_a.text_input("Student Full Name")
            grade = col_a.selectbox("Assign Grade", LEVEL_OPTIONS.get(sch_type, ["Grade 7"]))
            p_phone = col_b.text_input("Parent Phone Number (Required)")
            p_hint = col_b.text_input("Security Hint (e.g. Pet name)")
            
            st.warning("Note: Parent Phone will serve as the Parent's Login and Password.")
            
            if st.form_submit_button("Enroll Student & Register Parent"):
                if adm and name and p_phone:
                    # 1. Save Student
                    new_std = pd.DataFrame([[adm, name, grade, my_school, p_phone, CURRENT_YEAR]], columns=COLS["students"])
                    students = pd.concat([students, new_std], ignore_index=True)
                    save(students, "students")
                    
                    # 2. Save Student User Account
                    u_s = [adm, hash_password("1234"), "student", my_school, p_phone, "1234"]
                    # 3. Save Parent User Account
                    u_p = [p_phone, hash_password(p_phone), "parent", my_school, p_phone, p_hint]
                    
                    new_users = pd.DataFrame([u_s, u_p], columns=COLS["users"])
                    users = pd.concat([users, new_users], ignore_index=True).drop_duplicates('username', keep='last')
                    save(users, "users")
                    st.success(f"Success! Student {name} enrolled. Parent account {p_phone} created.")
                else: st.error("Please fill all required fields.")

    with t2:
        st.subheader("Add Teacher")
        tu, tp = st.text_input("Teacher Username"), st.text_input("Teacher Password", type="password")
        th = st.text_input("Password Recovery Hint")
        if st.button("Create Teacher Account"):
            t_acc = pd.DataFrame([[tu, hash_password(tp), "teacher", my_school, "000", th]], columns=COLS["users"])
            users = pd.concat([users, t_acc], ignore_index=True).drop_duplicates('username', keep='last')
            save(users, "users"); st.success(f"Teacher account '{tu}' ready.")

# =========================
# TEACHER: MARKS ENTRY (BULK)
# =========================
elif role == "teacher":
    sch_type = schools[schools.school_name == my_school].iloc[0]['type']
    st.header("📝 Performance Management")
    
    sel_cls = st.sidebar.selectbox("Select Grade", LEVEL_OPTIONS.get(sch_type, []))
    sel_term = st.sidebar.selectbox("Select Term", TERMS)
    
    t1, t2 = st.tabs(["Manual Entry", "Bulk Upload (CSV)"])
    
    cls_stds = students[(students.school == my_school) & (students['class'] == sel_cls)]
    
    if cls_stds.empty:
        st.info("No students enrolled in this grade yet.")
    else:
        with t1:
            subj = st.text_input("Subject Name (e.g., Mathematics)").strip()
            if subj:
                df_entry = pd.DataFrame({"adm_no": cls_stds.adm_no.values, "Name": cls_stds.name.values, "Marks": 0.0})
                edited = st.data_editor(df_entry, use_container_width=True, hide_index=True)
                if st.button("Save Manual Grades"):
                    new_rows = [[str(r['adm_no']), my_school, CURRENT_YEAR, sel_term, subj, r['Marks']] for _, r in edited.iterrows()]
                    marks = pd.concat([marks, pd.DataFrame(new_rows, columns=COLS["marks"])], ignore_index=True)
                    marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                    save(marks, "marks"); st.success("Grades saved.")

        with t2:
            st.subheader("Bulk Import via CSV")
            # Create template
            template = pd.DataFrame({"adm_no": cls_stds.adm_no.values, "subject": "Enter Subject", "marks": 0.0})
            csv = template.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV Template", data=csv, file_name=f"{sel_cls}_template.csv", mime="text/csv")
            
            uploaded_file = st.file_uploader("Upload filled template", type="csv")
            if uploaded_file:
                up_df = pd.read_csv(uploaded_file)
                if st.button("Confirm Bulk Upload"):
                    up_df['school'] = my_school
                    up_df['year'] = CURRENT_YEAR
                    up_df['term'] = sel_term
                    # Reorder to match COLS["marks"]
                    up_df = up_df[COLS["marks"]]
                    marks = pd.concat([marks, up_df], ignore_index=True)
                    marks = marks.drop_duplicates(subset=['adm_no', 'year', 'term', 'subject'], keep='last')
                    save(marks, "marks")
                    st.success("Bulk marks uploaded successfully.")

# =========================
# PARENT / STUDENT: HUB
# =========================
elif role in ["parent", "student"]:
    st.header("📊 Performance Hub")
    
    # Logic to fetch records
    search_val = logged_in_user['username']
    if role == 'parent':
        # Parents see all students linked to their phone
        my_records = students[students['parent_phone'] == search_val]
    else:
        # Students see only their own
        my_records = students[students['adm_no'] == search_val]
    
    if not my_records.empty:
        selected_adm = st.selectbox("Select Student Profile", my_records.adm_no.unique())
        std_info = my_records[my_records.adm_no == selected_adm].iloc[0]
        
        st.subheader(f"Academic Report: {std_info['name']}")
        st.markdown(f"**ADM:** {std_info['adm_no']} | **Grade:** {std_info['class']} | **School:** {std_info['school']}")
        
        std_marks = marks[(marks.adm_no == str(selected_adm)) & (marks.year == CURRENT_YEAR)]
        
        if not std_marks.empty:
            report = std_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last').fillna("-")
            st.table(report)
            
            st.divider()
            st.subheader("📈 Performance Trend")
            chart_data = std_marks.pivot_table(index='subject', columns='term', values='marks', aggfunc='last')
            st.bar_chart(chart_data)
        else:
            st.warning("No grades have been recorded for this student for the current year.")
    else:
        st.error("No student records are linked to this account.")

# =========================
# FINISHED
# =========================

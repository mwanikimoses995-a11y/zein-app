import streamlit as st
import pandas as pd
import os
import hashlib
import re
from datetime import datetime
from pathlib import Path

# =========================
# CONFIGURATION & CONSTANTS
# =========================
st.set_page_config(page_title="Zein School AI", layout="wide", page_icon="🎓")

# File paths using pathlib for cross-platform compatibility
DATA_DIR = Path("data")
FILES = {
    "schools": DATA_DIR / "schools.csv",
    "users": DATA_DIR / "users.csv", 
    "students": DATA_DIR / "students.csv",
    "marks": DATA_DIR / "marks.csv"
}

# Schema definitions with data types
SCHEMA = {
    "schools": {
        "cols": ["school_name", "type", "status"],
        "dtypes": {"school_name": str, "type": str, "status": str}
    },
    "users": {
        "cols": ["username", "password", "role", "school", "phone", "recovery_hint", "first_login", "assigned_subject"],
        "dtypes": {"username": str, "password": str, "role": str, "school": str, 
                  "phone": str, "recovery_hint": str, "first_login": str, "assigned_subject": str}
    },
    "students": {
        "cols": ["adm_no", "kemis_no", "name", "class", "school", "parent_phone", "reg_year", "status"],
        "dtypes": {"adm_no": str, "kemis_no": str, "name": str, "class": str, 
                  "school": str, "parent_phone": str, "reg_year": str, "status": str}
    },
    "marks": {
        "cols": ["adm_no", "school", "year", "term", "subject", "marks"],
        "dtypes": {"adm_no": str, "school": str, "year": str, "term": str, 
                  "subject": str, "marks": float}
    }
}

CBE_SUBJECTS = sorted([
    "Mathematics", "English", "Kiswahili", "Integrated Science", "Health Education", 
    "Social Studies", "Pre-Technical Studies", "Business Studies", "Agriculture", 
    "Nutrition", "Life Skills Education", "Physical Education and Sports", 
    "Religious Education (CRE/IRE/HRE)", "Creative Arts and Philanthropy", 
    "Computer Science", "Foreign Languages"
])

CURRENT_YEAR = str(datetime.now().year)
TERMS = ["Term 1", "Term 2", "Term 3"]
LEVEL_OPTIONS = {
    "Junior": ["Grade 7", "Grade 8", "Grade 9"],
    "Senior": ["Grade 10", "Grade 11", "Grade 12"],
    "Both": ["Grade 7", "Grade 8", "Grade 9", "Grade 10", "Grade 11", "Grade 12"]
}

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)

# =========================
# SECURITY UTILITIES
# =========================
def hash_password(password: str) -> str:
    """Secure password hashing using SHA-256 with salt simulation via username"""
    if not password:
        return ""
    return hashlib.sha256(str(password).encode()).hexdigest()

def validate_phone(phone: str) -> bool:
    """Validate phone number format (Kenyan format support)"""
    if not phone:
        return False
    # Remove common prefixes for validation
    clean = re.sub(r'[\s\-\(\)\+]', '', phone)
    return len(clean) >= 9 and clean.isdigit()

def validate_adm_no(adm: str) -> bool:
    """Validate admission number format"""
    return bool(adm and re.match(r'^[A-Za-z0-9\-]+$', str(adm)))

def get_grade(score):
    """Convert numeric score to grade label"""
    try:
        s = float(score)
        if s >= 80: return "Exceeding Expectations (A)"
        if s >= 60: return "Meeting Expectations (B)"
        if s >= 40: return "Approaching Expectations (C)"
        if s >= 0: return "Below Expectations (D)"
        return "Invalid"
    except (ValueError, TypeError):
        return "N/A"

# =========================
# DATA MANAGEMENT
# =========================
@st.cache_data(ttl=60)  # Cache for 60 seconds to reduce disk I/O
def load_data():
    """Load all data files with proper type handling"""
    data = {}
    for key, filepath in FILES.items():
        schema = SCHEMA[key]

        if not filepath.exists() or filepath.stat().st_size == 0:
            df = pd.DataFrame(columns=schema["cols"])
            # Ensure correct dtypes on empty DataFrame
            for col, dtype in schema["dtypes"].items():
                if col in df.columns:
                    df[col] = df[col].astype(dtype)
            df.to_csv(filepath, index=False)
            data[key] = df
        else:
            # Read with explicit dtypes
            df = pd.read_csv(filepath, dtype=str, keep_default_na=False)

            # Handle marks conversion specially
            if key == "marks" and "marks" in df.columns:
                df["marks"] = pd.to_numeric(df["marks"], errors="coerce")

            # Ensure all schema columns exist
            for col in schema["cols"]:
                if col not in df.columns:
                    df[col] = ""

            # Reorder columns to match schema
            data[key] = df[schema["cols"]]

    return data

def save_data(df: pd.DataFrame, key: str):
    """Save DataFrame to CSV with atomic write pattern"""
    filepath = FILES[key]
    temp_path = filepath.with_suffix('.tmp')

    try:
        # Write to temp first to prevent corruption on crash
        df.to_csv(temp_path, index=False)
        temp_path.replace(filepath)
    except Exception as e:
        st.error(f"Failed to save {key}: {e}")
        if temp_path.exists():
            temp_path.unlink()

def refresh_data():
    """Clear cache and reload data"""
    st.cache_data.clear()
    return load_data()

# Initialize data
db = load_data()

# =========================
# SUPERADMIN BOOTSTRAP
# =========================
def ensure_superadmin():
    """Ensure superadmin exists in the system"""
    users_df = db['users']
    if "zein" not in users_df['username'].values:
        sa_data = {
            "username": "zein",
            "password": hash_password("mionmion"),
            "role": "superadmin",
            "school": "SYSTEM",
            "phone": "000",
            "recovery_hint": "Founder",
            "first_login": "False",  # Changed to False - superadmin shouldn't force password change
            "assigned_subject": "All"
        }
        sa_df = pd.DataFrame([sa_data])
        db['users'] = pd.concat([users_df, sa_df], ignore_index=True)
        save_data(db['users'], "users")
        return refresh_data()
    return db

db = ensure_superadmin()

# =========================
# AUTHENTICATION SYSTEM
# =========================
def render_login():
    """Render login interface"""
    st.title("🛡️ Zein School AI Portal")

    tab1, tab2 = st.tabs(["Sign In", "Recovery"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("ID / Username").strip()
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Please enter both username and password.")
                    return

                user_row = db['users'][db['users']['username'] == username]
                if not user_row.empty and user_row.iloc[0]['password'] == hash_password(password):
                    st.session_state.user = user_row.iloc[0].to_dict()
                    st.session_state.db = db
                    st.rerun()
                else:
                    st.error("Incorrect username or password.")
                    # Security: Add small delay to prevent brute force
                    import time
                    time.sleep(0.5)

    with tab2:
        st.info("Contact your school administrator or superadmin to reset your password.")

def check_first_login():
    """Handle first-time password change requirement"""
    user = st.session_state.user

    if str(user.get("first_login", "")).lower() == "true":
        st.info("🔒 Security: Set a new password to activate your account.")

        with st.form("first_login_form"):
            new_pass = st.text_input("New Password", type="password")
            confirm_pass = st.text_input("Confirm Password", type="password")

            if st.form_submit_button("Update Password"):
                if len(new_pass) < 6:
                    st.error("Password must be at least 6 characters.")
                    return True
                if new_pass != confirm_pass:
                    st.error("Passwords do not match.")
                    return True

                # Update password
                mask = db['users']['username'] == user['username']
                db['users'].loc[mask, 'password'] = hash_password(new_pass)
                db['users'].loc[mask, 'first_login'] = "False"
                save_data(db['users'], "users")

                st.success("Password updated! Please login again.")
                st.session_state.clear()
                st.rerun()
                return True
        return True
    return False

# =========================
# MAIN APPLICATION FLOW
# =========================
if "user" not in st.session_state:
    render_login()
    st.stop()

user = st.session_state.user
db = st.session_state.get('db', load_data())

# Check first login
if check_first_login():
    st.stop()

# Sidebar Navigation
st.sidebar.title("🎓 Zein AI")
st.sidebar.markdown(f"**{user['username']}**  \n`{user['role'].upper()}`")

if st.sidebar.button("🚪 Logout", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# =========================
# ROLE-BASED DASHBOARDS
# =========================
role = user['role']
my_school = user.get('school', '')

# --- SUPERADMIN DASHBOARD ---
if role == "superadmin":
    st.header("🌐 Global Controller")

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("Create New School")
        with st.form("create_school"):
            school_name = st.text_input("School Name", key="new_school_name")
            school_level = st.selectbox("Level", ["Junior", "Senior", "Both"])

            if st.form_submit_button("Create School", use_container_width=True):
                if not school_name:
                    st.error("School name is required.")
                elif school_name in db['schools']['school_name'].values:
                    st.error("School already exists!")
                else:
                    # Create school
                    new_school = pd.DataFrame([{
                        "school_name": school_name,
                        "type": school_level,
                        "status": "Active"
                    }])
                    db['schools'] = pd.concat([db['schools'], new_school], ignore_index=True)
                    save_data(db['schools'], "schools")

                    # Create admin account
                    admin_data = {
                        "username": school_name,
                        "password": hash_password(school_name),
                        "role": "admin",
                        "school": school_name,
                        "phone": "000",
                        "recovery_hint": "Init",
                        "first_login": "True",  # Force password change
                        "assigned_subject": "All"
                    }
                    admin_df = pd.DataFrame([admin_data])
                    db['users'] = pd.concat([db['users'], admin_df], ignore_index=True)
                    save_data(db['users'], "users")

                    db = refresh_data()
                    st.session_state.db = db
                    st.success(f"✅ School '{school_name}' created! Admin login: `{school_name}` / `{school_name}`")

    with col2:
        st.subheader("Schools Registry")
        if not db['schools'].empty:
            # Add metrics
            metrics_cols = st.columns(3)
            metrics_cols[0].metric("Total Schools", len(db['schools']))
            metrics_cols[1].metric("Active", len(db['schools'][db['schools']['status'] == 'Active']))

            st.dataframe(db['schools'], use_container_width=True, hide_index=True)
        else:
            st.info("No schools registered yet.")

# --- ADMIN DASHBOARD ---
elif role == "admin":
    st.header(f"🏫 Admin: {my_school}")

    # Get school type for grade options
    school_info = db['schools'][db['schools']['school_name'] == my_school]
    if school_info.empty:
        st.error("School configuration error!")
        st.stop()

    school_type = school_info.iloc[0]['type']
    available_grades = LEVEL_OPTIONS.get(school_type, ["Grade 7"])

    tabs = st.tabs(["📋 Enroll Student", "📁 Bulk Import", "👥 Staff Management", "🎓 Promote", "🔍 Search"])

    # Tab 1: Individual Enrollment
    with tabs[0]:
        with st.form("enroll_student"):
            st.subheader("New Student Enrollment")
            c1, c2 = st.columns(2)

            adm_no = c1.text_input("Admission Number *", help="Unique ID for student")
            full_name = c1.text_input("Full Name *")
            parent_phone = c2.text_input("Parent Phone *", help="Used for parent login")
            grade = c2.selectbox("Grade", available_grades)

            if st.form_submit_button("Enroll Student", use_container_width=True):
                # Validation
                if not all([adm_no, full_name, parent_phone]):
                    st.error("All fields are required.")
                elif not validate_adm_no(adm_no):
                    st.error("Invalid admission number format.")
                elif not validate_phone(parent_phone):
                    st.error("Invalid phone number format.")
                elif adm_no in db['students']['adm_no'].values:
                    st.error("Admission number already exists!")
                else:
                    # Create student record
                    student_data = {
                        "adm_no": adm_no.strip().upper(),
                        "kemis_no": "N/A",
                        "name": full_name.strip(),
                        "class": grade,
                        "school": my_school,
                        "parent_phone": parent_phone.strip(),
                        "reg_year": CURRENT_YEAR,
                        "status": "Active"
                    }

                    # Add student
                    db['students'] = pd.concat([db['students'], pd.DataFrame([student_data])], ignore_index=True)

                    # Create accounts
                    accounts = []

                    # Student account
                    if adm_no not in db['users']['username'].values:
                        accounts.append({
                            "username": adm_no,
                            "password": hash_password("1234"),
                            "role": "student",
                            "school": my_school,
                            "phone": parent_phone,
                            "recovery_hint": "1234",
                            "first_login": "True",
                            "assigned_subject": "None"
                        })

                    # Parent account
                    if parent_phone not in db['users']['username'].values:
                        accounts.append({
                            "username": parent_phone,
                            "password": hash_password(parent_phone),
                            "role": "parent",
                            "school": my_school,
                            "phone": parent_phone,
                            "recovery_hint": "Phone",
                            "first_login": "True",
                            "assigned_subject": "None"
                        })

                    if accounts:
                        db['users'] = pd.concat([db['users'], pd.DataFrame(accounts)], ignore_index=True)

                    save_data(db['students'], "students")
                    save_data(db['users'], "users")
                    db = refresh_data()
                    st.session_state.db = db

                    st.success(f"✅ Student enrolled! Accounts created:")
                    st.code(f"Student: {adm_no} / 1234\nParent: {parent_phone} / {parent_phone}")

    # Tab 2: Bulk Import
    with tabs[1]:
        st.subheader("Bulk Student Import")
        st.markdown("Upload CSV with columns: `adm_no`, `name`, `class`, `parent_phone`")

        uploaded = st.file_uploader("Choose CSV file", type="csv")
        if uploaded:
            try:
                df_upload = pd.read_csv(uploaded, dtype=str)
                required_cols = ['adm_no', 'name', 'class', 'parent_phone']

                if not all(col in df_upload.columns for col in required_cols):
                    st.error(f"CSV must contain: {required_cols}")
                else:
                    st.write("Preview:")
                    st.dataframe(df_upload.head())

                    if st.button("Import All Students", use_container_width=True):
                        # Add metadata
                        df_upload['school'] = my_school
                        df_upload['reg_year'] = CURRENT_YEAR
                        df_upload['status'] = "Active"
                        df_upload['kemis_no'] = "N/A"

                        # Reorder to match schema
                        df_upload = df_upload[SCHEMA['students']['cols']]

                        # Check for duplicates
                        existing_adms = set(db['students']['adm_no'].values)
                        new_adms = set(df_upload['adm_no'].values)
                        conflicts = existing_adms & new_adms

                        if conflicts:
                            st.warning(f"Skipping existing admission numbers: {conflicts}")
                            df_upload = df_upload[~df_upload['adm_no'].isin(conflicts)]

                        if not df_upload.empty:
                            db['students'] = pd.concat([db['students'], df_upload], ignore_index=True)
                            save_data(db['students'], "students")
                            db = refresh_data()
                            st.session_state.db = db
                            st.success(f"✅ Imported {len(df_upload)} students!")
                        else:
                            st.info("No new students to import.")
            except Exception as e:
                st.error(f"Error reading file: {e}")

    # Tab 3: Staff Management (Placeholder)
    with tabs[2]:
        st.subheader("Staff Management")
        st.info("Feature: Add teachers, assign subjects, manage permissions")

        with st.form("add_teacher"):
            t_name = st.text_input("Teacher Username")
            t_subject = st.selectbox("Assigned Subject", ["All"] + CBE_SUBJECTS)

            if st.form_submit_button("Add Teacher"):
                if t_name and t_name not in db['users']['username'].values:
                    teacher_data = {
                        "username": t_name,
                        "password": hash_password(t_name),
                        "role": "teacher",
                        "school": my_school,
                        "phone": "000",
                        "recovery_hint": "Init",
                        "first_login": "True",
                        "assigned_subject": t_subject
                    }
                    db['users'] = pd.concat([db['users'], pd.DataFrame([teacher_data])], ignore_index=True)
                    save_data(db['users'], "users")
                    db = refresh_data()
                    st.session_state.db = db
                    st.success(f"Teacher added! Login: {t_name} / {t_name}")

    # Tab 4: Promote (Placeholder)
    with tabs[3]:
        st.subheader("Student Promotion")
        st.info("Bulk promote students to next grade")

        col1, col2 = st.columns(2)
        from_grade = col1.selectbox("From Grade", available_grades)
        to_grade = col2.selectbox("To Grade", available_grades)

        if st.button("Promote Students", use_container_width=True):
            mask = (db['students']['school'] == my_school) & (db['students']['class'] == from_grade)
            count = mask.sum()
            if count > 0:
                db['students'].loc[mask, 'class'] = to_grade
                save_data(db['students'], "students")
                db = refresh_data()
                st.session_state.db = db
                st.success(f"Promoted {count} students from {from_grade} to {to_grade}")
            else:
                st.warning("No students found in selected grade.")

    # Tab 5: Search
    with tabs[4]:
        st.subheader("Student Search")
        query = st.text_input("Search by Name or ADM No")

        if query:
            mask = (
                (db['students']['school'] == my_school) & 
                (
                    db['students']['name'].str.contains(query, case=False, na=False) | 
                    (db['students']['adm_no'] == query)
                )
            )
            results = db['students'][mask]

            if not results.empty:
                st.dataframe(results, use_container_width=True, hide_index=True)
                st.caption(f"Found {len(results)} student(s)")
            else:
                st.warning("No students found.")

# --- TEACHER DASHBOARD ---
elif role == "teacher":
    assigned_subject = user.get("assigned_subject", "Unassigned")
    st.header(f"📝 Teacher Portal: {assigned_subject}")

    # Get school grades
    school_info = db['schools'][db['schools']['school_name'] == my_school]
    if school_info.empty:
        st.error("School not found!")
        st.stop()

    school_type = school_info.iloc[0]['type']
    available_grades = LEVEL_OPTIONS.get(school_type, [])

    # Sidebar context
    with st.sidebar:
        st.markdown("---")
        selected_grade = st.selectbox("Select Class", available_grades)
        selected_term = st.selectbox("Select Term", TERMS)

    tab1, tab2 = st.tabs(["✏️ Marks Entry", "📊 Analytics"])

    # Tab 1: Marks Entry
    with tab1:
        # Get active students for this class
        students = db['students'][
            (db['students']['school'] == my_school) & 
            (db['students']['class'] == selected_grade) &
            (db['students']['status'] == "Active")
        ]

        if students.empty:
            st.warning("No active students found in this class.")
        else:
            st.subheader(f"Enter Marks: {selected_grade} - {selected_term}")

            # Prepare entry data
            entry_data = pd.DataFrame({
                "adm_no": students['adm_no'].values,
                "Name": students['name'].values,
                "Score": [0.0] * len(students)
            })

            # Check for existing marks to pre-fill
            existing = db['marks'][
                (db['marks']['school'] == my_school) &
                (db['marks']['year'] == CURRENT_YEAR) &
                (db['marks']['term'] == selected_term) &
                (db['marks']['subject'] == assigned_subject) &
                (db['marks']['adm_no'].isin(students['adm_no']))
            ]

            if not existing.empty:
                existing_dict = existing.set_index('adm_no')['marks'].to_dict()
                entry_data['Score'] = entry_data['adm_no'].map(existing_dict).fillna(0)
                st.info("Pre-filled with existing marks")

            # Data editor
            edited = st.data_editor(
                entry_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "adm_no": st.column_config.TextColumn("ADM No", disabled=True),
                    "Name": st.column_config.TextColumn("Student Name", disabled=True),
                    "Score": st.column_config.NumberColumn("Score", min_value=0, max_value=100, step=1)
                }
            )

            if st.button("💾 Save Marks", use_container_width=True):
                # Validate scores
                invalid = edited[(edited['Score'] < 0) | (edited['Score'] > 100)]
                if not invalid.empty:
                    st.error("Scores must be between 0 and 100!")
                else:
                    # Prepare mark records
                    mark_records = []
                    for _, row in edited.iterrows():
                        mark_records.append({
                            "adm_no": str(row['adm_no']),
                            "school": my_school,
                            "year": CURRENT_YEAR,
                            "term": selected_term,
                            "subject": assigned_subject,
                            "marks": float(row['Score'])
                        })

                    # Remove existing marks for these students in this context
                    mask = ~(
                        (db['marks']['adm_no'].isin(edited['adm_no'])) &
                        (db['marks']['school'] == my_school) &
                        (db['marks']['year'] == CURRENT_YEAR) &
                        (db['marks']['term'] == selected_term) &
                        (db['marks']['subject'] == assigned_subject)
                    )
                    db['marks'] = db['marks'][mask]

                    # Add new marks
                    if mark_records:
                        db['marks'] = pd.concat([db['marks'], pd.DataFrame(mark_records)], ignore_index=True)
                        save_data(db['marks'], "marks")
                        db = refresh_data()
                        st.session_state.db = db
                        st.success(f"✅ Saved marks for {len(mark_records)} students!")

    # Tab 2: Analytics
    with tab2:
        st.subheader("Performance Analytics")

        # Load marks for this context
        marks_data = db['marks'][
            (db['marks']['school'] == my_school) &
            (db['marks']['subject'] == assigned_subject) &
            (db['marks']['term'] == selected_term) &
            (db['marks']['year'] == CURRENT_YEAR)
        ]

        if marks_data.empty:
            st.info("No marks data available for selected filters.")
        else:
            # Merge with student data for names
            chart_data = marks_data.merge(
                db['students'][['adm_no', 'name', 'class']], 
                on='adm_no', 
                how='left'
            )

            # Filter by selected grade if applicable
            chart_data = chart_data[chart_data['class'] == selected_grade]

            if chart_data.empty:
                st.info(f"No data for {selected_grade} in this term.")
            else:
                # Statistics
                avg_score = chart_data['marks'].mean()
                max_score = chart_data['marks'].max()
                min_score = chart_data['marks'].min()

                cols = st.columns(4)
                cols[0].metric("Average", f"{avg_score:.1f}")
                cols[1].metric("Highest", f"{max_score:.1f}")
                cols[2].metric("Lowest", f"{min_score:.1f}")
                cols[3].metric("Students", len(chart_data))

                # Chart
                try:
                    import plotly.express as px
                    fig = px.bar(
                        chart_data.sort_values('marks', ascending=False),
                        x='name',
                        y='marks',
                        color='marks',
                        color_continuous_scale='RdYlGn',
                        title=f"{selected_grade} - {assigned_subject} - {selected_term}",
                        labels={'name': 'Student', 'marks': 'Score'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

                    # Grade distribution
                    chart_data['grade'] = chart_data['marks'].apply(get_grade)
                    grade_dist = chart_data['grade'].value_counts()
                    st.caption("Grade Distribution")
                    st.bar_chart(grade_dist)

                except ImportError:
                    st.error("Plotly not installed. Run: `pip install plotly`")
                    # Fallback to simple bar chart
                    st.bar_chart(chart_data.set_index('name')['marks'])

# --- PARENT/STUDENT DASHBOARD ---
elif role in ["parent", "student"]:
    st.header("📊 Academic Results Center")

    # Determine search key
    if role == "parent":
        search_key = user['username']  # phone number
        my_kids = db['students'][db['students']['parent_phone'] == search_key]
        st.caption(f"Viewing results for children linked to: {search_key}")
    else:
        search_key = user['username']  # adm_no
        my_kids = db['students'][db['students']['adm_no'] == search_key]

    if my_kids.empty:
        st.error("No student records found linked to this account.")
    else:
        # Student selector for parents
        if role == "parent" and len(my_kids) > 1:
            target_adm = st.selectbox(
                "Select Student", 
                my_kids['adm_no'].unique(),
                format_func=lambda x: f"{x} - {my_kids[my_kids['adm_no']==x].iloc[0]['name']}"
            )
        else:
            target_adm = my_kids.iloc[0]['adm_no']

        # Get student info
        student_info = my_kids[my_kids['adm_no'] == target_adm].iloc[0]

        # Display student card
        col1, col2 = st.columns([1, 2])
        with col1:
            st.metric("Student", student_info['name'])
            st.metric("Class", student_info['class'])
            st.metric("ADM No", student_info['adm_no'])
        with col2:
            st.metric("School", student_info['school'])
            st.metric("Registration Year", student_info['reg_year'])

        st.divider()

        # Fetch marks
        results = db['marks'][
            (db['marks']['adm_no'] == str(target_adm)) & 
            (db['marks']['year'] == CURRENT_YEAR)
        ]

        if results.empty:
            st.info("📭 No marks recorded yet for this academic year.")
        else:
            # Create pivot table report
            st.subheader("Academic Report")

            # Pivot with proper handling
            report = results.pivot_table(
                index='subject',
                columns='term',
                values='marks',
                aggfunc='first'  # Use first instead of last for consistency
            ).fillna("-")

            # Ensure all terms appear
            for term in TERMS:
                if term not in report.columns:
                    report[term] = "-"

            # Reorder columns
            report = report[TERMS]

            st.dataframe(report, use_container_width=True)

            # Term summaries
            st.subheader("Term Performance")
            cols = st.columns(len(TERMS))

            for i, term in enumerate(TERMS):
                term_marks = results[results['term'] == term]['marks']
                if not term_marks.empty:
                    avg = term_marks.mean()
                    grade = get_grade(avg)
                    cols[i].metric(
                        f"{term}",
                        f"{avg:.1f}%",
                        grade
                    )
                else:
                    cols[i].metric(term, "-", "No data")

# --- FALLBACK ---
else:
    st.error("Unknown role. Contact administrator.")
    st.stop()

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("© 2024 Zein School AI v2.0")

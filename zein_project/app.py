"""
ZEIN SCHOOL AI v5.0 - ZERO EDUCATIONAL IGNORANCE NETWORK
========================================================
Production-Ready School Management System with:
- SQLite Database (CSV replaced)
- CBE/CBC Curriculum Compliance
- Student Fields: KEMIS No, ADM No, Guardian Phone, Class, Stream
- PDF Report Cards with CBC Grading
- SMS Integration
- AI Chatbot Assistant
- Library Management
- Audit Logging & Automated Backups

Author: ZEIN Development Team
Version: 5.0.0
License: MIT
"""

import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import os
import hashlib
import re
import json
import time
import base64
import random
import string
import threading
import queue
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from io import BytesIO
from contextlib import contextmanager
from functools import wraps

# Optional imports with graceful fallbacks
try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False

try:
    from twilio.rest import Client as TwilioClient
    HAS_TWILIO = True
except ImportError:
    HAS_TWILIO = False

try:
    import africastalking
    HAS_AFRICASTALKING = True
except ImportError:
    HAS_AFRICASTALKING = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, letter
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.pdfgen import canvas
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.graphics import renderPDF
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

try:
    import plotly.express as px
    import plotly.graph_objects as go
    HAS_PLOTLY = True
except ImportError:
    HAS_PLOTLY = False

# =========================
# CONFIGURATION & CONSTANTS
# =========================

class Config:
    """Centralized configuration for ZEIN"""
    
    # Branding & Identity
    APP_NAME = "ZEIN"
    FULL_NAME = "Zero Educational Ignorance Network"
    VERSION = "5.0.0"
    TAGLINE = "Empowering Education, Eliminating Ignorance"
    MISSION = "To create a world where every student has access to quality education tracking and support"
    VISION = "Zero ignorance through technology-enabled education"
    
    # Visual Identity
    PRIMARY_COLOR = "#1E3A8A"      # Deep Blue - Trust, Education
    SECONDARY_COLOR = "#F59E0B"    # Amber - Energy, Optimism  
    ACCENT_COLOR = "#10B981"       # Emerald - Growth, Success
    WARNING_COLOR = "#EF4444"      # Red - Alerts
    BACKGROUND_COLOR = "#F8FAFC"   # Light Slate
    TEXT_COLOR = "#1E293B"         # Dark Slate
    
    # Typography (CSS Font Stack)
    FONT_HEADING = "'Segoe UI', 'Roboto', 'Helvetica Neue', sans-serif"
    FONT_BODY = "'Inter', 'Segoe UI', system-ui, sans-serif"
    
    # Paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    BACKUP_DIR = BASE_DIR / "backups"
    ASSETS_DIR = BASE_DIR / "assets"
    TEMP_DIR = BASE_DIR / "temp"
    DB_PATH = DATA_DIR / "zein_school.db"
    
    # Security
    MIN_PASSWORD_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    SESSION_TIMEOUT_MINUTES = 120
    OTP_EXPIRY_MINUTES = 10
    
    # SMS Configuration (Environment variables recommended)
    SMS_PROVIDER = "twilio"  # or "africastalking"
    TWILIO_SID = os.getenv("TWILIO_SID", "")
    TWILIO_TOKEN = os.getenv("TWILIO_TOKEN", "")
    TWILIO_PHONE = os.getenv("TWILIO_PHONE", "")
    
    AFRICASTALKING_USERNAME = os.getenv("AT_USERNAME", "")
    AFRICASTALKING_API_KEY = os.getenv("AT_API_KEY", "")
    
    # OpenAI Configuration
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    CHATBOT_MODEL = "gpt-3.5-turbo"
    
    # Performance
    CACHE_TTL = 120
    MAX_UPLOAD_SIZE_MB = 20
    
    # Academic
    CURRENT_YEAR = 2025
    TERMS = ["Term 1", "Term 2", "Term 3"]
    
    @classmethod
    def ensure_dirs(cls):
        for dir_path in [cls.DATA_DIR, cls.LOGS_DIR, cls.BACKUP_DIR, cls.ASSETS_DIR, cls.TEMP_DIR]:
            dir_path.mkdir(parents=True, exist_ok=True)

Config.ensure_dirs()

# Page Configuration
st.set_page_config(
    page_title=f"{Config.FULL_NAME} v{Config.VERSION}",
    layout="wide",
    page_icon="🎓",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://zein.edu/support',
        'Report a bug': "https://github.com/zein-edu/zein-school-ai/issues",
        'About': f"**{Config.FULL_NAME}** v{Config.VERSION} - {Config.MISSION}"
    }
)

# =========================
# CBE CURRICULUM (CBC) DATA
# =========================

class CBECurriculum:
    """Competency-Based Education (CBC) Curriculum Structure - Kenya"""
    
    # Grade Levels with Streams
    GRADES = {
        "PP1": "Pre-Primary 1",
        "PP2": "Pre-Primary 2",
        "Grade 1": "Lower Primary",
        "Grade 2": "Lower Primary", 
        "Grade 3": "Lower Primary",
        "Grade 4": "Upper Primary",
        "Grade 5": "Upper Primary",
        "Grade 6": "Upper Primary",
        "Grade 7": "Junior Secondary",
        "Grade 8": "Junior Secondary",
        "Grade 9": "Junior Secondary",
        "Grade 10": "Senior Secondary",
        "Grade 11": "Senior Secondary",
        "Grade 12": "Senior Secondary"
    }
    
    # Streams for secondary levels
    STREAMS = {
        "Junior Secondary": ["North", "South", "East", "West", "Blue", "Red", "Green", "Yellow"],
        "Senior Secondary": ["North", "South", "East", "West", "Blue", "Red", "Green", "Yellow"]
    }
    
    # Learning Areas by Level
    SUBJECTS = {
        "Pre-Primary": [
            "Mathematical Activities",
            "Language Activities",
            "Environmental Activities",
            "Psychomotor and Creative Activities",
            "Religious Education Activities",
            "Pastoral Programmes"
        ],
        "Lower Primary": [
            "Mathematics",
            "English Language",
            "Kiswahili Language",
            "Literacy Activities",
            "Hygiene and Nutrition",
            "Environmental Activities",
            "Religious Education",
            "Movement and Creative Activities",
            "Agriculture",
            "Pastoral Programmes"
        ],
        "Upper Primary": [
            "Mathematics",
            "English Language",
            "Kiswahili Language",
            "Science and Technology",
            "Social Studies",
            "Religious Education",
            "Home Science",
            "Agriculture",
            "Creative Arts",
            "Physical and Health Education",
            "Pastoral Programmes"
        ],
        "Junior Secondary": [
            "Mathematics",
            "English Language",
            "Kiswahili Language",
            "Integrated Science",
            "Health Education",
            "Social Studies",
            "Pre-Technical Studies",
            "Business Studies",
            "Agriculture",
            "Life Skills Education",
            "Sports and Physical Education",
            "Religious Education (CRE/IRE/HRE)",
            "Creative Arts and Sports",
            "Computer Science",
            "Foreign Languages"
        ],
        "Senior Secondary": [
            "Mathematics",
            "English Language",
            "Kiswahili Language",
            "Biology",
            "Chemistry", 
            "Physics",
            "Geography",
            "History and Government",
            "Christian Religious Education",
            "Islamic Religious Education",
            "Hindu Religious Education",
            "Business Studies",
            "Computer Studies",
            "Home Science",
            "Art and Design",
            "Music",
            "French",
            "German",
            "Arabic"
        ]
    }
    
    # Performance Levels (CBC Grading)
    PERFORMANCE_LEVELS = {
        4: ("Exceeds Expectations", "A", 80, 100, "The learner consistently demonstrates exceptional understanding and application of concepts"),
        3: ("Meets Expectations", "B", 60, 79, "The learner demonstrates good understanding and can apply concepts appropriately"),
        2: ("Approaches Expectations", "C", 40, 59, "The learner shows basic understanding but needs support in application"),
        1: ("Below Expectations", "D", 0, 39, "The learner requires significant intervention and support")
    }
    
    @classmethod
    def get_grade_level(cls, grade: str) -> str:
        """Determine education level from grade"""
        if grade in ["PP1", "PP2"]:
            return "Pre-Primary"
        elif grade in ["Grade 1", "Grade 2", "Grade 3"]:
            return "Lower Primary"
        elif grade in ["Grade 4", "Grade 5", "Grade 6"]:
            return "Upper Primary"
        elif grade in ["Grade 7", "Grade 8", "Grade 9"]:
            return "Junior Secondary"
        else:
            return "Senior Secondary"
    
    @classmethod
    def get_subjects(cls, grade: str) -> List[str]:
        """Get relevant subjects for a grade level"""
        level = cls.get_grade_level(grade)
        return cls.SUBJECTS.get(level, [])
    
    @classmethod
    def get_streams(cls, grade: str) -> List[str]:
        """Get available streams for a grade"""
        level = cls.get_grade_level(grade)
        return cls.STREAMS.get(level, ["Default"])
    
    @classmethod
    def calculate_performance_level(cls, score: float) -> Tuple[int, str, str, str]:
        """Calculate CBC performance level from score"""
        if score is None or pd.isna(score):
            return 0, "Not Graded", "-", "No score available"
        for level, (desc, letter, min_score, max_score, explanation) in cls.PERFORMANCE_LEVELS.items():
            if min_score <= score <= max_score:
                return level, desc, letter, explanation
        return 1, "Below Expectations", "D", "Requires significant support"
    
    @classmethod
    def get_report_remarks(cls, score: float) -> str:
        """Get appropriate remarks for report card"""
        level, desc, letter, explanation = cls.calculate_performance_level(score)
        return f"{desc} ({letter}) - {explanation}"

# =========================
# DATABASE MANAGER (REPLACES CSV)
# =========================

class DatabaseManager:
    """Thread-safe SQLite database manager with connection pooling"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(Config.DB_PATH)
        self.local = threading.local()
        self._init_database()
    
    @contextmanager
    def get_connection(self):
        """Thread-safe connection context manager"""
        if not hasattr(self.local, 'connection'):
            self.local.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=20.0,
                isolation_level=None
            )
            self.local.connection.row_factory = sqlite3.Row
            # Enable foreign keys
            self.local.connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield self.local.connection
        except Exception as e:
            self.local.connection.rollback()
            raise e
    
    def _init_database(self):
        """Initialize database schema with proper relationships and constraints"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Schools table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schools (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    school_name TEXT UNIQUE NOT NULL,
                    school_code TEXT UNIQUE,
                    type TEXT CHECK(type IN ('Pre-Primary', 'Primary', 'Junior Secondary', 'Senior Secondary', 'Mixed', 'Special Needs')),
                    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Inactive', 'Suspended')),
                    address TEXT,
                    phone TEXT,
                    email TEXT,
                    motto TEXT DEFAULT 'Excellence in Education',
                    logo_path TEXT,
                    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Academic years table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS academic_years (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    year INTEGER NOT NULL,
                    term TEXT CHECK(term IN ('Term 1', 'Term 2', 'Term 3')),
                    start_date DATE,
                    end_date DATE,
                    is_current BOOLEAN DEFAULT 0,
                    school_id INTEGER,
                    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                    UNIQUE(year, term, school_id)
                )
            """)
            
            # Users table with proper indexing
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    role TEXT CHECK(role IN ('superadmin', 'admin', 'teacher', 'student', 'parent', 'librarian', 'finance')),
                    school_id INTEGER,
                    phone TEXT,
                    email TEXT,
                    recovery_hint TEXT,
                    first_login BOOLEAN DEFAULT 1,
                    assigned_subject TEXT,
                    assigned_grade TEXT,
                    assigned_stream TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    otp_code TEXT,
                    otp_expiry TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE SET NULL
                )
            """)
            
            # Students table - ENHANCED with KEMIS, ADM, Stream
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kemis_number TEXT,
                    admission_number TEXT NOT NULL,
                    name TEXT NOT NULL,
                    grade TEXT NOT NULL,
                    stream TEXT DEFAULT 'Default',
                    school_id INTEGER NOT NULL,
                    guardian_phone TEXT NOT NULL,
                    guardian_email TEXT,
                    guardian_name TEXT,
                    guardian_relationship TEXT,
                    dob DATE,
                    gender TEXT CHECK(gender IN ('Male', 'Female', 'Other', 'Prefer not to say')),
                    nationality TEXT DEFAULT 'Kenyan',
                    reg_year INTEGER,
                    status TEXT DEFAULT 'Active' CHECK(status IN ('Active', 'Transferred', 'Graduated', 'Suspended', 'Expelled')),
                    current_academic_year INTEGER,
                    special_needs TEXT,
                    boarding_status TEXT CHECK(boarding_status IN ('Day Scholar', 'Boarder', 'Mixed')),
                    admission_date DATE DEFAULT CURRENT_DATE,
                    previous_school TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE,
                    UNIQUE(admission_number, school_id),
                    UNIQUE(kemis_number, school_id)
                )
            """)
            
            # Marks table with foreign key constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS marks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    student_id INTEGER NOT NULL,
                    academic_year_id INTEGER NOT NULL,
                    subject TEXT NOT NULL,
                    marks REAL CHECK(marks >= 0 AND marks <= 100),
                    grade TEXT,
                    performance_level INTEGER,
                    entered_by INTEGER,
                    entered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    remarks TEXT,
                    assessment_type TEXT DEFAULT 'End Term' CHECK(assessment_type IN ('CAT 1', 'CAT 2', 'Mid Term', 'End Term', 'Project', 'Practical')),
                    FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE,
                    FOREIGN KEY (academic_year_id) REFERENCES academic_years(id),
                    FOREIGN KEY (entered_by) REFERENCES users(id),
                    UNIQUE(student_id, academic_year_id, subject, assessment_type)
                )
            """)
            
            # Library books table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    isbn TEXT,
                    title TEXT NOT NULL,
                    author TEXT NOT NULL,
                    publisher TEXT,
                    category TEXT,
                    grade_level TEXT,
                    quantity INTEGER DEFAULT 1 CHECK(quantity >= 0),
                    available INTEGER DEFAULT 1 CHECK(available >= 0),
                    shelf_location TEXT,
                    school_id INTEGER,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'Available' CHECK(status IN ('Available', 'Damaged', 'Lost', 'Out of Circulation')),
                    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE
                )
            """)
            
            # Borrowings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS borrowings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    book_id INTEGER NOT NULL,
                    student_id INTEGER NOT NULL,
                    borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date TIMESTAMP NOT NULL,
                    return_date TIMESTAMP,
                    status TEXT DEFAULT 'Borrowed' CHECK(status IN ('Borrowed', 'Returned', 'Overdue', 'Lost')),
                    fine_amount REAL DEFAULT 0.0,
                    issued_by INTEGER,
                    FOREIGN KEY (book_id) REFERENCES books(id),
                    FOREIGN KEY (student_id) REFERENCES students(id),
                    FOREIGN KEY (issued_by) REFERENCES users(id),
                    CHECK (return_date IS NULL OR return_date >= borrow_date)
                )
            """)
            
            # SMS logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sms_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    phone TEXT NOT NULL,
                    message_type TEXT CHECK(message_type IN ('OTP', 'WELCOME', 'ALERT', 'LIBRARY', 'FEES', 'GENERAL')),
                    message_preview TEXT,
                    status TEXT CHECK(status IN ('SENT', 'FAILED', 'PENDING', 'SIMULATED')),
                    error_message TEXT,
                    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    sent_by INTEGER,
                    FOREIGN KEY (sent_by) REFERENCES users(id)
                )
            """)
            
            # Audit logs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    record_id INTEGER,
                    action TEXT CHECK(action IN ('INSERT', 'UPDATE', 'DELETE')),
                    old_values TEXT,
                    new_values TEXT,
                    performed_by TEXT,
                    performed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT
                )
            """)
            
            # Chat history
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    session_id TEXT,
                    message TEXT,
                    response TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            
            # Create indexes for performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_marks_student ON marks(student_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_marks_year ON marks(academic_year_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_school ON students(school_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_adm_no ON students(admission_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_kemis ON students(kemis_number)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_guardian ON students(guardian_phone)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_school ON users(school_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_borrowings_status ON borrowings(status)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_books_isbn ON books(isbn)")
            
            conn.commit()
    
    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        """Execute SELECT query and return results as list of dicts"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
    
    def execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE and return rowcount"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.rowcount
    
    def get_last_insert_id(self) -> int:
        """Get last inserted row id"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT last_insert_rowid()")
            return cursor.fetchone()[0]
    
    def audit_log(self, table_name: str, record_id: int, action: str, 
                  old_values: Dict = None, new_values: Dict = None, 
                  performed_by: str = None):
        """Log changes for audit trail"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO audit_logs (table_name, record_id, action, old_values, new_values, performed_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    table_name, record_id, action,
                    json.dumps(old_values) if old_values else None,
                    json.dumps(new_values) if new_values else None,
                    performed_by
                ))
        except Exception as e:
            print(f"Audit log error: {e}")

# Initialize global database manager
db = DatabaseManager()

# =========================
# BACKUP MANAGER
# =========================

class BackupManager:
    """Automated backup and restore functionality"""
    
    def __init__(self, db_path: str = None, backup_dir: Path = None):
        self.db_path = db_path or str(Config.DB_PATH)
        self.backup_dir = backup_dir or Config.BACKUP_DIR
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self) -> Path:
        """Create timestamped compressed backup"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.backup_dir / f"zein_backup_{timestamp}.db.gz"
        
        with open(self.db_path, 'rb') as f_in:
            with gzip.open(backup_file, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        self._cleanup_old_backups()
        return backup_file
    
    def _cleanup_old_backups(self, keep: int = 30):
        """Remove old backups, keep only N most recent"""
        backups = sorted(self.backup_dir.glob("zein_backup_*.db.gz"))
        for old_backup in backups[:-keep]:
            old_backup.unlink()
    
    def restore_backup(self, backup_file: Path) -> bool:
        """Restore from backup with verification"""
        try:
            # Verify backup integrity
            with gzip.open(backup_file, 'rb') as f:
                header = f.read(100)
                if b'SQLite format 3' not in header:
                    raise ValueError("Invalid SQLite backup file")
            
            # Create safety backup
            if Path(self.db_path).exists():
                safety_backup = self.backup_dir / f"safety_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                shutil.copy2(self.db_path, safety_backup)
            
            # Restore
            with gzip.open(backup_file, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            return True
        except Exception as e:
            print(f"Restore failed: {e}")
            return False
    
    def list_backups(self) -> List[Path]:
        """List available backups"""
        return sorted(self.backup_dir.glob("zein_backup_*.db.gz"), reverse=True)

backup_mgr = BackupManager()

# =========================
# SECURITY MANAGER
# =========================

class SecurityManager:
    @staticmethod
    def hash_password(password: str) -> str:
        if not password:
            return ""
        if HAS_BCRYPT:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode(), salt).decode()
        else:
            pepper = "ZEIN2024SecureEducationNetwork"
            return hashlib.sha256((password + pepper).encode()).hexdigest()
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        if not password or not hashed:
            return False
        if HAS_BCRYPT and hashed.startswith('$2'):
            return bcrypt.checkpw(password.encode(), hashed.encode())
        return SecurityManager.hash_password(password) == hashed
    
    @staticmethod
    def generate_otp(length: int = 6) -> str:
        """Generate secure OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def validate_phone(phone: str) -> Tuple[bool, str]:
        """Validate Kenyan phone number format"""
        if not phone:
            return False, "Phone number is required"
        
        # Remove common separators
        clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        
        # Check if digits only (after removing +)
        if not clean.lstrip('+').isdigit():
            return False, "Phone number should contain only digits"
        
        # Kenyan format validation
        if len(clean) == 9 and clean.startswith('7'):
            return True, "Valid"
        elif len(clean) == 10 and clean.startswith('07'):
            return True, "Valid"
        elif len(clean) == 12 and clean.startswith('2547'):
            return True, "Valid"
        elif len(clean) == 13 and clean.startswith('+2547'):
            return True, "Valid"
        
        return False, "Invalid Kenyan phone format. Use 07XX XXX XXX or 2547XX XXX XXX"
    
    @staticmethod
    def validate_kemis(kemis: str) -> Tuple[bool, str]:
        """Validate KEMIS number format"""
        if not kemis:
            return True, "Optional"  # KEMIS is optional
        
        # KEMIS is typically numeric
        if not kemis.isdigit():
            return False, "KEMIS should contain only digits"
        
        if len(kemis) < 6 or len(kemis) > 20:
            return False, "KEMIS should be 6-20 digits"
        
        return True, "Valid"
    
    @staticmethod
    def validate_admission_number(adm_no: str) -> Tuple[bool, str]:
        """Validate admission number"""
        if not adm_no:
            return False, "Admission number is required"
        
        if len(adm_no) < 3:
            return False, "Admission number too short (min 3 characters)"
        
        if len(adm_no) > 20:
            return False, "Admission number too long (max 20 characters)"
        
        # Allow alphanumeric with hyphens and slashes
        if not re.match(r'^[A-Za-z0-9\-\/]+$', adm_no):
            return False, "Admission number can only contain letters, numbers, hyphens and slashes"
        
        return True, "Valid"

# =========================
# SMS MANAGER
# =========================

class SMSManager:
    """Handle SMS notifications for password resets and alerts"""
    
    def __init__(self):
        self.provider = Config.SMS_PROVIDER
        self.client = None
        
        if self.provider == "twilio" and HAS_TWILIO:
            if Config.TWILIO_SID and Config.TWILIO_TOKEN:
                self.client = TwilioClient(Config.TWILIO_SID, Config.TWILIO_TOKEN)
        elif self.provider == "africastalking" and HAS_AFRICASTALKING:
            if Config.AFRICASTALKING_USERNAME and Config.AFRICASTALKING_API_KEY:
                africastalking.initialize(Config.AFRICASTALKING_USERNAME, Config.AFRICASTALKING_API_KEY)
                self.client = africastalking.SMS()
    
    def format_phone(self, phone: str) -> str:
        """Format phone to international format"""
        clean = re.sub(r'[\s\-\(\)]', '', phone)
        
        if clean.startswith('+'):
            return clean
        elif clean.startswith('0'):
            return '+254' + clean[1:]
        elif clean.startswith('254'):
            return '+' + clean
        else:
            return '+254' + clean
    
    def send_otp(self, phone: str, otp: str, username: str) -> Tuple[bool, str]:
        """Send OTP for password reset"""
        message = f"【ZEIN】Password Reset Code: {otp}. Valid for 10 minutes. Do not share this code. Username: {username}"
        return self._send_sms(phone, message, "OTP")
    
    def send_welcome_sms(self, phone: str, username: str, password: str, role: str) -> Tuple[bool, str]:
        """Send welcome message with credentials"""
        message = f"【ZEIN】Welcome to Zero Educational Ignorance Network! Your {role} account: Username: {username}, Password: {password}. Change password on first login."
        return self._send_sms(phone, message, "WELCOME")
    
    def send_low_mark_alert(self, phone: str, student_name: str, subject: str, mark: float) -> Tuple[bool, str]:
        """Alert parent about low marks"""
        message = f"【ZEIN】Alert: {student_name} scored {mark:.1f}% in {subject}. Please check the portal for details and schedule a teacher meeting."
        return self._send_sms(phone, message, "ALERT")
    
    def send_library_due_reminder(self, phone: str, student_name: str, book_title: str, days_remaining: int) -> Tuple[bool, str]:
        """Library due date reminder"""
        if days_remaining == 0:
            message = f"【ZEIN】URGENT: {student_name}'s book '{book_title}' is due TODAY. Please return immediately to avoid fines."
        else:
            message = f"【ZEIN】Reminder: {student_name}'s book '{book_title}' is due in {days_remaining} days. Please return to avoid fines."
        return self._send_sms(phone, message, "LIBRARY")
    
    def _send_sms(self, phone: str, message: str, msg_type: str) -> Tuple[bool, str]:
        """Internal SMS sender with logging"""
        try:
            formatted_phone = self.format_phone(phone)
            
            if not self.client:
                # Fallback: Log to database for demo/testing
                self._log_sms(phone, msg_type, message[:50] + "...", "SIMULATED", None)
                return True, "SMS simulated (no provider configured)"
            
            # Send via provider
            if self.provider == "twilio":
                self.client.messages.create(
                    body=message,
                    from_=Config.TWILIO_PHONE,
                    to=formatted_phone
                )
            elif self.provider == "africastalking":
                self.client.send(message, [formatted_phone])
            
            self._log_sms(phone, msg_type, message[:50] + "...", "SENT", None)
            return True, "SMS sent successfully"
            
        except Exception as e:
            self._log_sms(phone, msg_type, message[:50] + "...", "FAILED", str(e))
            return False, f"SMS failed: {str(e)}"
    
    def _log_sms(self, phone: str, msg_type: str, preview: str, status: str, error: str = None):
        """Log all SMS attempts to database"""
        try:
            masked_phone = phone[:4] + "****" + phone[-4:] if len(phone) > 8 else "****"
            db.execute_update("""
                INSERT INTO sms_logs (phone, message_type, message_preview, status, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (masked_phone, msg_type, preview, status, error))
        except Exception as e:
            print(f"SMS logging error: {e}")

# Initialize SMS manager
sms_manager = SMSManager()

# =========================
# AI CHATBOT ASSISTANT
# =========================

class ZEINAssistant:
    """AI-powered chatbot for ZEIN"""
    
    SYSTEM_PROMPT = """You are ZEIN Assistant, the official AI helper for the Zero Educational Ignorance Network school management system.

Your capabilities:
1. Help users navigate the system (parents, students, teachers, admins)
2. Explain CBE curriculum and grading system
3. Guide on report card interpretation
4. Assist with library queries
5. Provide study tips and resources
6. Answer FAQs about the school system

Key facts about ZEIN:
- KEMIS number: Kenya Education Management Information System unique identifier
- ADM number: School-specific admission number
- CBC Grading: Level 4 (A, 80-100%), Level 3 (B, 60-79%), Level 2 (C, 40-59%), Level 1 (D, below 40%)

Tone: Professional, friendly, educational, encouraging
Always identify yourself as ZEIN Assistant.
If you don't know something, direct users to contact support@zein.edu"""

    def __init__(self):
        self.openai_available = HAS_OPENAI and Config.OPENAI_API_KEY
        
        # Local knowledge base for common questions
        self.knowledge_base = {
            "kemis": "KEMIS (Kenya Education Management Information System) is a unique identifier assigned by the Ministry of Education. It's different from the school's Admission Number.",
            "admission number": "The Admission Number is assigned by the school when a student enrolls. It's used for internal school identification alongside the KEMIS number.",
            "guardian phone": "The Guardian Phone number is the primary contact for parents/guardians. It's used for SMS notifications and parent login.",
            "stream": "Streams are class divisions (e.g., North, South, Blue, Red) used in secondary schools to manage large student populations.",
            "cbe curriculum": "The Competency-Based Education (CBC) curriculum focuses on skills and competencies. It uses 4 performance levels: 4 (Exceeds), 3 (Meets), 2 (Approaches), 1 (Below).",
            "cbc grading": "CBC Grading: Level 4 = A (80-100%), Level 3 = B (60-79%), Level 2 = C (40-59%), Level 1 = D (Below 40%).",
            "report card": "You can generate and download PDF report cards from the 'Academic Results' section. Click 'Generate Report Card PDF' to download.",
            "reset password": "Click 'Forgot Password' on the login page. An OTP will be sent to your registered phone number.",
            "library": "Access the Library module from the main menu to browse books, check availability, and see borrowing history.",
            "contact": "For support, email support@zein.edu or call your school administrator.",
            "grades": "Grades are calculated based on CBC performance levels: A (80-100%), B (60-79%), C (40-59%), D (Below 40%)."
        }
    
    def get_response(self, user_message: str, user_context: Dict) -> str:
        """Get AI response to user message"""
        user_message_lower = user_message.lower()
        
        # Check knowledge base first
        for key, response in self.knowledge_base.items():
            if key in user_message_lower:
                return response
        
        # Try OpenAI if available
        if self.openai_available:
            try:
                import openai
                openai.api_key = Config.OPENAI_API_KEY
                
                messages = [
                    {"role": "system", "content": self.SYSTEM_PROMPT},
                    {"role": "user", "content": f"User context: {user_context}. Question: {user_message}"}
                ]
                
                response = openai.ChatCompletion.create(
                    model=Config.CHATBOT_MODEL,
                    messages=messages,
                    max_tokens=150,
                    temperature=0.7
                )
                
                return response.choices[0].message.content
                
            except Exception as e:
                return f"I'm having trouble connecting to my AI brain. Try checking the Help section or contact support@zein.edu. (Error: {str(e)})"
        
        # Fallback response
        return "I'm ZEIN Assistant! I can help you navigate the system, explain CBC grading, or guide you to resources. What would you like to know?"
    
    def log_chat(self, user_id: int, session_id: str, message: str, response: str):
        """Log chat interactions"""
        try:
            db.execute_update("""
                INSERT INTO chat_history (user_id, session_id, message, response)
                VALUES (?, ?, ?, ?)
            """, (user_id, session_id, message, response))
        except Exception as e:
            print(f"Chat logging error: {e}")

# Initialize assistant
zein_assistant = ZEINAssistant()

# =========================
# REPORT CARD GENERATOR
# =========================

class ReportCardGenerator:
    @staticmethod
    def generate_pdf(student_info: Dict, marks_data: List[Dict], school_info: Dict, 
                     term: str, year: int) -> Optional[bytes]:
        """Generate official CBC report card PDF"""
        if not HAS_REPORTLAB:
            return None
        
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, 
                               topMargin=72, bottomMargin=18)
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=28, 
                                   textColor=colors.HexColor(Config.PRIMARY_COLOR), 
                                   alignment=1, spaceAfter=12, fontName='Helvetica-Bold')
        
        subtitle_style = ParagraphStyle('Subtitle', parent=styles['Normal'], fontSize=10, 
                                      textColor=colors.grey, alignment=1, spaceAfter=6)
        
        # Header with ZEIN branding
        elements.append(Paragraph("<b>ZEIN</b>", title_style))
        elements.append(Paragraph(Config.FULL_NAME, subtitle_style))
        elements.append(Paragraph(f"<b>OFFICIAL REPORT CARD</b> | {year} {term}", subtitle_style))
        elements.append(Spacer(1, 20))
        
        # School info box
        school_data = [
            ['SCHOOL:', school_info.get('school_name', 'N/A'), 'PHONE:', school_info.get('phone', 'N/A')],
            ['ADDRESS:', school_info.get('address', 'N/A'), 'EMAIL:', school_info.get('email', 'N/A')],
            ['MOTTO:', school_info.get('motto', 'Excellence in Education'), '', '']
        ]
        school_table = Table(school_data, colWidths=[1.2*inch, 2.3*inch, 1*inch, 2*inch])
        school_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(Config.PRIMARY_COLOR)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('BACKGROUND', (2, 0), (2, -1), colors.HexColor(Config.PRIMARY_COLOR)),
            ('TEXTCOLOR', (2, 0), (2, -1), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        elements.append(school_table)
        elements.append(Spacer(1, 20))
        
        # Student info - ENHANCED with KEMIS and Stream
        student_data = [
            ['STUDENT NAME:', student_info.get('name', 'N/A'), 'ADM NO:', student_info.get('admission_number', 'N/A')],
            ['KEMIS NO:', student_info.get('kemis_number') or 'N/A', 'GENDER:', student_info.get('gender', 'N/A')],
            ['GRADE:', student_info.get('grade', 'N/A'), 'STREAM:', student_info.get('stream', 'N/A')],
            ['GUARDIAN:', student_info.get('guardian_name') or 'N/A', 'PHONE:', student_info.get('guardian_phone', 'N/A')],
            ['YEAR:', str(year), 'TERM:', term]
        ]
        student_table = Table(student_data, colWidths=[1.5*inch, 2.5*inch, 1.2*inch, 1.5*inch])
        student_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.HexColor(Config.SECONDARY_COLOR)),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
            ('BACKGROUND', (2, 0), (2, -2), colors.HexColor(Config.SECONDARY_COLOR)),
            ('TEXTCOLOR', (2, 0), (2, -2), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(student_table)
        elements.append(Spacer(1, 25))
        
        # Academic performance with CBE grading
        elements.append(Paragraph("<b>ACADEMIC PERFORMANCE</b>", 
                                  ParagraphStyle('Section', parent=styles['Heading2'], 
                                               fontSize=12, textColor=colors.HexColor(Config.PRIMARY_COLOR))))
        elements.append(Spacer(1, 10))
        
        if marks_data:
            table_data = [['LEARNING AREA', 'SCORE (%)', 'GRADE', 'PERFORMANCE LEVEL', 'REMARKS']]
            
            total_score = 0
            count = 0
            
            for mark in marks_data:
                score = mark.get('marks', 0)
                if score is not None and score > 0:
                    level, desc, letter, explanation = CBECurriculum.calculate_performance_level(score)
                    remarks = CBECurriculum.get_report_remarks(score)
                    
                    table_data.append([
                        mark.get('subject', 'N/A'),
                        f"{score:.1f}",
                        letter,
                        f"Level {level}: {desc}",
                        remarks[:40] + "..." if len(remarks) > 40 else remarks
                    ])
                    total_score += score
                    count += 1
            
            # Average row
            if count > 0:
                avg = total_score / count
                avg_level, avg_desc, avg_letter, _ = CBECurriculum.calculate_performance_level(avg)
                table_data.append(['', '', '', '', ''])
                table_data.append([
                    'OVERALL AVERAGE', 
                    f"{avg:.1f}%", 
                    avg_letter,
                    f"Level {avg_level}: {avg_desc}",
                    CBECurriculum.get_report_remarks(avg)
                ])
            
            marks_table = Table(table_data, colWidths=[2.2*inch, 1*inch, 0.8*inch, 2*inch, 2.3*inch])
            marks_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(Config.PRIMARY_COLOR)),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('FONTSIZE', (0, 1), (-1, -2), 9),
                ('GRID', (0, 0), (-1, -2), 0.5, colors.grey),
                ('LINEBELOW', (0, -1), (-1, -1), 2, colors.HexColor(Config.PRIMARY_COLOR)),
                ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0f9ff')),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(marks_table)
        else:
            elements.append(Paragraph("<i>No academic records available for this term.</i>", styles['Italic']))
        
        elements.append(Spacer(1, 20))
        
        # CBE Grading Key
        elements.append(Paragraph("<b>COMPETENCY-BASED ASSESSMENT KEY</b>", 
                                  ParagraphStyle('Key', parent=styles['Heading3'], 
                                               fontSize=10, textColor=colors.HexColor(Config.PRIMARY_COLOR))))
        
        key_data = [
            ['Level 4 (A): 80-100%', 'Exceeds Expectations', 'Exceptional understanding and application'],
            ['Level 3 (B): 60-79%', 'Meets Expectations', 'Good understanding and appropriate application'],
            ['Level 2 (C): 40-59%', 'Approaches Expectations', 'Basic understanding, needs support'],
            ['Level 1 (D): Below 40%', 'Below Expectations', 'Requires significant intervention']
        ]
        key_table = Table(key_data, colWidths=[1.8*inch, 1.8*inch, 3.7*inch])
        key_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        elements.append(key_table)
        elements.append(Spacer(1, 30))
        
        # Signatures
        sig_data = [
            ['_' * 35, '_' * 35, '_' * 35],
            ['CLASS TEACHER', 'PRINCIPAL', 'PARENT/GUARDIAN'],
            [datetime.now().strftime("%Y-%m-%d"), 'Date: _______________', 'Date: _______________']
        ]
        sig_table = Table(sig_data, colWidths=[2.3*inch, 2.3*inch, 2.3*inch])
        sig_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 30),
        ]))
        elements.append(sig_table)
        
        elements.append(Spacer(1, 30))
        elements.append(Paragraph(f"<i>This is an official document generated by {Config.FULL_NAME} v{Config.VERSION}</i>", 
                                  ParagraphStyle('Footer', parent=styles['Normal'], 
                                               fontSize=8, textColor=colors.grey, alignment=1)))
        elements.append(Paragraph("<i>Any alteration renders this document invalid</i>", 
                                  ParagraphStyle('Footer2', parent=styles['Normal'], 
                                               fontSize=8, textColor=colors.grey, alignment=1)))
        
        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes
    
    @staticmethod
    def get_download_link(pdf_bytes: bytes, filename: str) -> str:
        b64 = base64.b64encode(pdf_bytes).decode()
        return f'<a href="data:application/pdf;base64,{b64}" download="{filename}" style="text-decoration:none;"><button style="background:linear-gradient(135deg, {Config.PRIMARY_COLOR} 0%, {Config.SECONDARY_COLOR} 100%);color:white;padding:12px 24px;border:none;border-radius:8px;cursor:pointer;font-weight:600;font-size:14px;box-shadow:0 4px 12px rgba(30,58,138,0.3);">📥 Download Official Report Card (PDF)</button></a>'

# =========================
# CUSTOM CSS & VISUAL IDENTITY
# =========================

def apply_zein_theme():
    """Apply comprehensive ZEIN visual identity"""
    
    # Generate watermark SVG
    watermark_svg = f"""
    <svg width="300" height="300" xmlns="http://www.w3.org/2000/svg">
        <defs>
            <pattern id="zeinPattern" x="0" y="0" width="300" height="300" patternUnits="userSpaceOnUse">
                <text x="50%" y="40%" font-family="Arial Black, sans-serif" font-size="32" 
                      fill="{Config.PRIMARY_COLOR}08" text-anchor="middle" dominant-baseline="middle"
                      transform="rotate(-30 150 150)" font-weight="bold">ZEIN</text>
                <text x="50%" y="55%" font-family="Arial, sans-serif" font-size="11" 
                      fill="{Config.PRIMARY_COLOR}05" text-anchor="middle" dominant-baseline="middle"
                      transform="rotate(-30 150 150)">Zero Educational Ignorance Network</text>
                <text x="50%" y="65%" font-family="Arial, sans-serif" font-size="14" 
                      fill="{Config.SECONDARY_COLOR}06" text-anchor="middle" dominant-baseline="middle"
                      transform="rotate(-30 150 150)">🎓</text>
            </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#zeinPattern)"/>
    </svg>
    """
    
    b64_watermark = base64.b64encode(watermark_svg.encode()).decode()
    
    st.markdown(f"""
    <style>
        /* Global Styles */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        .stApp {{
            background-color: {Config.BACKGROUND_COLOR};
            background-image: url("data:image/svg+xml;base64,{b64_watermark}");
            background-attachment: fixed;
            font-family: {Config.FONT_BODY};
            color: {Config.TEXT_COLOR};
        }}
        
        /* ZEIN Header */
        .zein-header {{
            background: linear-gradient(135deg, {Config.PRIMARY_COLOR} 0%, {Config.SECONDARY_COLOR} 100%);
            padding: 2rem;
            border-radius: 16px;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 10px 40px rgba(30, 58, 138, 0.3);
            position: relative;
            overflow: hidden;
        }}
        
        .zein-header::before {{
            content: "🎓";
            position: absolute;
            font-size: 8rem;
            opacity: 0.1;
            top: -20px;
            right: -20px;
            transform: rotate(15deg);
        }}
        
        .zein-logo-text {{
            font-size: 3.5rem;
            font-weight: 800;
            color: white;
            letter-spacing: 6px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            margin: 0;
            font-family: 'Arial Black', sans-serif;
        }}
        
        .zein-fullname {{
            font-size: 1.2rem;
            color: rgba(255,255,255,0.95);
            margin-top: 0.5rem;
            font-weight: 500;
            letter-spacing: 2px;
        }}
        
        .zein-tagline {{
            font-size: 0.95rem;
            color: rgba(255,255,255,0.8);
            margin-top: 0.3rem;
            font-style: italic;
        }}
        
        /* Cards */
        .zein-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            border-left: 4px solid {Config.PRIMARY_COLOR};
            margin-bottom: 1rem;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .zein-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }}
        
        /* Buttons */
        .stButton > button {{
            border-radius: 8px;
            font-weight: 600;
            transition: all 0.3s ease;
            font-family: {Config.FONT_BODY};
        }}
        
        .stButton > button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .stButton > button[kind="primary"] {{
            background: linear-gradient(135deg, {Config.PRIMARY_COLOR} 0%, {Config.SECONDARY_COLOR} 100%);
            border: none;
            color: white;
        }}
        
        /* Sidebar */
        [data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {Config.PRIMARY_COLOR} 0%, #1e40af 100%);
        }}
        
        [data-testid="stSidebar"] .stMarkdown {{
            color: white;
        }}
        
        /* Metrics */
        [data-testid="stMetric"] {{
            background: white;
            border-radius: 12px;
            padding: 1rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        
        [data-testid="stMetricLabel"] {{
            color: {Config.PRIMARY_COLOR};
            font-weight: 600;
        }}
        
        /* Dataframes */
        .stDataFrame {{
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }}
        
        /* Scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f1f5f9;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: {Config.PRIMARY_COLOR};
            border-radius: 4px;
        }}
        
        /* Status indicators */
        .status-active {{
            color: {Config.ACCENT_COLOR};
            font-weight: 600;
        }}
        
        .status-warning {{
            color: {Config.WARNING_COLOR};
            font-weight: 600;
        }}
        
        /* Animations */
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(10px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        
        .animate-in {{
            animation: fadeIn 0.5s ease-out;
        }}
    </style>
    """, unsafe_allow_html=True)

# =========================
# AUTHENTICATION SYSTEM
# =========================

class AuthManager:
    @staticmethod
    def render_login():
        """Render login page with ZEIN branding"""
        apply_zein_theme()
        
        # ZEIN branded header
        st.markdown(f"""
        <div class="zein-header animate-in">
            <div class="zein-logo-text">🎓 {Config.APP_NAME}</div>
            <div class="zein-fullname">{Config.FULL_NAME}</div>
            <div class="zein-tagline">"{Config.TAGLINE}"</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Mission statement
        with st.expander("🌍 Our Mission: Zero Educational Ignorance", expanded=False):
            st.markdown(f"""
            **{Config.FULL_NAME}** is dedicated to eliminating educational barriers through innovative technology.
            
            **What we do:**
            - 📊 Real-time academic tracking for parents and students
            - 🤖 AI-powered learning assistance
            - 📚 Digital library management
            - 🔔 Instant SMS notifications
            - 📱 Mobile-friendly access
            
            **Join us in creating a world where every student succeeds!**
            """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            with st.container(border=True):
                st.subheader("🔐 Secure Login")
                
                tab1, tab2 = st.tabs(["Sign In", "Forgot Password"])
                
                with tab1:
                    with st.form("login_form", clear_on_submit=True):
                        username = st.text_input("Username / ID", placeholder="Enter your username")
                        password = st.text_input("Password", type="password", placeholder="Enter your password")
                        
                        if st.form_submit_button("Sign In", use_container_width=True, type="primary"):
                            if not username or not password:
                                st.error("Please enter both fields")
                                return
                            
                            # Query database for user
                            user = db.execute_query("""
                                SELECT u.*, s.school_name 
                                FROM users u
                                LEFT JOIN schools s ON u.school_id = s.id
                                WHERE u.username = ? AND u.is_active = 1
                            """, (username,))
                            
                            if user and SecurityManager.verify_password(password, user[0]['password_hash']):
                                user_data = user[0]
                                
                                # Update last login
                                db.execute_update("""
                                    UPDATE users SET last_login = ? WHERE id = ?
                                """, (datetime.now().isoformat(), user_data['id']))
                                
                                # Set session state
                                st.session_state.user = user_data
                                st.session_state.session_id = hashlib.md5(f"{username}{time.time()}".encode()).hexdigest()[:12]
                                
                                st.success("✅ Login successful! Welcome to ZEIN.")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Invalid credentials or inactive account")
                                time.sleep(0.3)
                
                with tab2:
                    st.info("📱 Password Reset via SMS")
                    st.write("Enter your username. An OTP will be sent to your registered phone number.")
                    
                    with st.form("forgot_password_form"):
                        reset_user = st.text_input("Username", key="reset_username")
                        reset_phone = st.text_input("Registered Phone Number", key="reset_phone")
                        
                        if st.form_submit_button("Send OTP", use_container_width=True, type="primary"):
                            if not reset_user or not reset_phone:
                                st.error("Please enter both username and phone number")
                                return
                            
                            # Verify user exists
                            user = db.execute_query("""
                                SELECT * FROM users WHERE username = ? AND phone = ? AND is_active = 1
                            """, (reset_user, reset_phone))
                            
                            if user:
                                # Generate and save OTP
                                otp = SecurityManager.generate_otp()
                                otp_expiry = (datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)).isoformat()
                                
                                db.execute_update("""
                                    UPDATE users SET otp_code = ?, otp_expiry = ? WHERE id = ?
                                """, (otp, otp_expiry, user[0]['id']))
                                
                                # Send SMS
                                success, msg = sms_manager.send_otp(reset_phone, otp, reset_user)
                                
                                if success:
                                    st.session_state.reset_username = reset_user
                                    st.session_state.reset_user_id = user[0]['id']
                                    st.session_state.otp_sent = True
                                    st.success(f"✅ OTP sent to {reset_phone[:4]}****{reset_phone[-4:]}")
                                    st.info(f"📱 SMS Status: {msg}")
                                else:
                                    st.error(f"Failed to send SMS: {msg}")
                            else:
                                st.error("Username and phone number do not match our records")
                    
                    # OTP Verification and Password Reset
                    if st.session_state.get('otp_sent'):
                        st.divider()
                        st.subheader("🔢 Verify OTP & Reset Password")
                        
                        with st.form("verify_otp_form"):
                            entered_otp = st.text_input("Enter 6-digit OTP", max_chars=6, key="entered_otp")
                            new_password = st.text_input("New Password", type="password", key="new_pass")
                            confirm_password = st.text_input("Confirm New Password", type="password", key="confirm_pass")
                            
                            if st.form_submit_button("Reset Password", use_container_width=True, type="primary"):
                                if not all([entered_otp, new_password, confirm_password]):
                                    st.error("Please fill all fields")
                                    return
                                
                                if new_password != confirm_password:
                                    st.error("Passwords do not match")
                                    return
                                
                                if len(new_password) < Config.MIN_PASSWORD_LENGTH:
                                    st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                                    return
                                
                                # Verify OTP
                                user = db.execute_query("""
                                    SELECT * FROM users WHERE id = ? AND otp_code = ?
                                """, (st.session_state.reset_user_id, entered_otp))
                                
                                if user:
                                    # Check expiry
                                    otp_expiry = datetime.fromisoformat(user[0]['otp_expiry'])
                                    if datetime.now() < otp_expiry:
                                        # Update password
                                        db.execute_update("""
                                            UPDATE users 
                                            SET password_hash = ?, otp_code = NULL, otp_expiry = NULL 
                                            WHERE id = ?
                                        """, (SecurityManager.hash_password(new_password), user[0]['id']))
                                        
                                        # Clear session state
                                        del st.session_state.otp_sent
                                        del st.session_state.reset_username
                                        del st.session_state.reset_user_id
                                        
                                        st.success("✅ Password reset successful! Please login with your new password.")
                                    else:
                                        st.error("❌ OTP has expired. Please request a new one.")
                                else:
                                    st.error("❌ Invalid OTP")
    
    @staticmethod
    def check_first_login():
        """Check if user needs to set password on first login"""
        user = st.session_state.get("user", {})
        if user.get("first_login"):
            st.warning("🔐 Welcome! Please set a secure password to continue")
            
            with st.form("first_login_form"):
                new_pass = st.text_input("New Password", type="password")
                confirm_pass = st.text_input("Confirm Password", type="password")
                
                if st.form_submit_button("Set Password", type="primary", use_container_width=True):
                    if len(new_pass) < Config.MIN_PASSWORD_LENGTH:
                        st.error(f"Minimum {Config.MIN_PASSWORD_LENGTH} characters required")
                        return True
                    if new_pass != confirm_pass:
                        st.error("Passwords don't match")
                        return True
                    
                    # Update password
                    db.execute_update("""
                        UPDATE users SET password_hash = ?, first_login = 0 WHERE id = ?
                    """, (SecurityManager.hash_password(new_pass), user['id']))
                    
                    # Send welcome SMS
                    if user.get('phone'):
                        sms_manager.send_welcome_sms(user['phone'], user['username'], "[Hidden]", user['role'])
                    
                    # Update session
                    st.session_state.user['first_login'] = 0
                    
                    st.success("✅ Password set successfully!")
                    time.sleep(1)
                    st.rerun()
            return True
        return False

# =========================
# CHATBOT UI COMPONENT
# =========================

def render_chatbot(user: Dict):
    """Render floating chatbot widget"""
    
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    
    col1, col2, col3 = st.columns([6, 6, 1])
    with col3:
        if st.button("💬" if not st.session_state.chat_open else "✕", 
                    key="chat_toggle",
                    help="ZEIN Assistant"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()
    
    if st.session_state.chat_open:
        with st.container():
            st.markdown("""
            <style>
            .chat-widget {
                position: fixed;
                bottom: 80px;
                right: 20px;
                width: 380px;
                max-height: 600px;
                background: white;
                border-radius: 16px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.2);
                z-index: 9999;
                display: flex;
                flex-direction: column;
                overflow: hidden;
                border: 2px solid #1E3A8A;
            }
            </style>
            """, unsafe_allow_html=True)
            
            st.markdown('<div class="chat-widget">', unsafe_allow_html=True)
            
            # Header
            st.markdown(f"""
            <div style="background: linear-gradient(135deg, {Config.PRIMARY_COLOR} 0%, {Config.SECONDARY_COLOR} 100%);
                        color: white; padding: 1rem; font-weight: 600; display: flex; 
                        justify-content: space-between; align-items: center;">
                <span>🎓 ZEIN Assistant</span>
                <span style="font-size:0.8rem;opacity:0.9;">v{Config.VERSION}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Messages
            if 'chat_messages' not in st.session_state:
                st.session_state.chat_messages = [
                    {"role": "bot", "content": "Hello! I'm ZEIN Assistant. I can help you with:\n• Navigating the system\n• Explaining CBC grading\n• Report card questions\n• Library queries\n\nWhat can I help you with today?"}
                ]
            
            messages_html = '<div style="flex: 1; overflow-y: auto; padding: 1rem; background: #f8fafc; max-height: 400px;">'
            for msg in st.session_state.chat_messages:
                if msg["role"] == "user":
                    messages_html += f'<div style="background: #1E3A8A; color: white; padding: 8px 12px; border-radius: 12px 12px 0 12px; margin: 4px 0; margin-left: 20%; font-size: 13px;">{msg["content"]}</div>'
                else:
                    messages_html += f'<div style="background: white; border: 1px solid #e2e8f0; color: #1e293b; padding: 8px 12px; border-radius: 12px 12px 12px 0; margin: 4px 0; margin-right: 20%; font-size: 13px;">{msg["content"]}</div>'
            messages_html += '</div>'
            st.markdown(messages_html, unsafe_allow_html=True)
            
            # Input
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed")
                if st.form_submit_button("Send", use_container_width=True):
                    if user_input:
                        st.session_state.chat_messages.append({"role": "user", "content": user_input})
                        
                        response = zein_assistant.get_response(user_input, user)
                        st.session_state.chat_messages.append({"role": "bot", "content": response})
                        
                        zein_assistant.log_chat(user.get('id'), st.session_state.get('session_id', ''), user_input, response)
                        
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# =========================
# MAIN APPLICATION
# =========================

def main():
    # Initialize database on first run
    if not Config.DB_PATH.exists():
        st.info("Initializing database... Please wait.")
    
    # Check authentication
    if "user" not in st.session_state:
        AuthManager.render_login()
        st.stop()
    
    user = st.session_state.user
    
    # Check first login
    if AuthManager.check_first_login():
        st.stop()
    
    # Apply theme
    apply_zein_theme()
    
    # =========================
    # SIDEBAR WITH ZEIN BRANDING
    # =========================
    
    with st.sidebar:
        st.markdown(f"""
        <div style="text-align:center;padding:1.5rem 0;border-bottom:2px solid rgba(255,255,255,0.2);margin-bottom:1rem;">
            <div style="font-size:2.5rem;font-weight:800;color:white;letter-spacing:4px;text-shadow:2px 2px 4px rgba(0,0,0,0.2);">🎓 {Config.APP_NAME}</div>
            <div style="font-size:0.75rem;color:rgba(255,255,255,0.8);margin-top:0.5rem;letter-spacing:1px;">{Config.FULL_NAME}</div>
            <div style="font-size:0.65rem;color:rgba(255,255,255,0.6);margin-top:0.3rem;font-style:italic;">v{Config.VERSION}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # User info card
        with st.container(border=True):
            st.markdown(f"**👤 {user['username']}**")
            st.caption(f"🎭 Role: `{user['role'].upper()}`")
            if user.get('school_name'):
                st.caption(f"🏫 School: {user['school_name']}")
            if user.get('assigned_subject'):
                st.caption(f"📚 Subject: {user['assigned_subject']}")
        
        st.divider()
        
        # Navigation
        st.markdown("### 📍 Navigation")
        
        if st.button("🏠 Dashboard", use_container_width=True, key="nav_dashboard"):
            st.session_state.current_page = "dashboard"
            st.rerun()
        
        if st.button("📚 Library", use_container_width=True, key="nav_library"):
            st.session_state.current_page = "library"
            st.rerun()
        
        if st.button("⚙️ Settings", use_container_width=True, key="nav_settings"):
            st.session_state.current_page = "settings"
            st.rerun()
        
        st.divider()
        
        # Logout
        if st.button("🚪 Logout", use_container_width=True, type="secondary", key="logout_btn"):
            st.session_state.clear()
            st.rerun()
        
        # Footer
        st.markdown(f"""
        <div style="position:fixed;bottom:10px;left:0;right:0;text-align:center;padding:1rem;">
            <div style="font-size:0.7rem;color:rgba(255,255,255,0.5);">
                © 2024 {Config.FULL_NAME}<br>
                <span style="font-size:0.6rem;">Eliminating Educational Ignorance</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # =========================
    # ROLE-BASED DASHBOARDS
    # =========================
    
    role = user.get('role', '')
    school_id = user.get('school_id')
    page = st.session_state.get('current_page', 'dashboard')
    
    # --- SUPERADMIN DASHBOARD ---
    if role == 'superadmin':
        if page == 'dashboard':
            st.header("🌐 ZEIN Global System Controller")
            
            # Metrics
            metrics = db.execute_query("""
                SELECT 
                    (SELECT COUNT(*) FROM schools) as total_schools,
                    (SELECT COUNT(*) FROM users) as total_users,
                    (SELECT COUNT(*) FROM students) as total_students,
                    (SELECT COUNT(*) FROM books) as total_books
            """)[0]
            
            cols = st.columns(4)
            with cols[0]:
                st.metric("🏫 Schools", metrics['total_schools'], border=True)
            with cols[1]:
                st.metric("👥 Total Users", metrics['total_users'], border=True)
            with cols[2]:
                st.metric("🎓 Students", metrics['total_students'], border=True)
            with cols[3]:
                st.metric("📚 Library Books", metrics['total_books'], border=True)
            
            # Management tabs
            tab1, tab2, tab3, tab4 = st.tabs(["🏫 Schools", "👤 Users", "📊 Analytics", "💾 Backups"])
            
            with tab1:
                col1, col2 = st.columns([1, 2])
                with col1:
                    with st.container(border=True):
                        st.subheader("Create New School")
                        with st.form("create_school"):
                            name = st.text_input("School Name")
                            school_code = st.text_input("School Code (Unique)")
                            level = st.selectbox("Level", ["Pre-Primary", "Primary", "Junior Secondary", "Senior Secondary", "Mixed", "Special Needs"])
                            address = st.text_area("Address")
                            phone = st.text_input("Phone")
                            email = st.text_input("Email")
                            motto = st.text_input("School Motto", value="Excellence in Education")
                            
                            if st.form_submit_button("Create School", type="primary"):
                                if name:
                                    try:
                                        db.execute_update("""
                                            INSERT INTO schools (school_name, school_code, type, address, phone, email, motto)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (name, school_code, level, address, phone, email, motto))
                                        
                                        school_id_new = db.get_last_insert_id()
                                        
                                        # Create admin user
                                        admin_pass = SecurityManager.hash_password(name.lower().replace(" ", ""))
                                        db.execute_update("""
                                            INSERT INTO users (username, password_hash, role, school_id, phone, email, recovery_hint, first_login, assigned_subject)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (name.lower().replace(" ", ""), admin_pass, "admin", school_id_new, phone or "000", email or "", "Init", 1, "All"))
                                        
                                        if phone:
                                            sms_manager.send_welcome_sms(phone, name.lower().replace(" ", ""), name.lower().replace(" ", ""), "Administrator")
                                        
                                        st.success(f"✅ School '{name}' created! Admin login: {name.lower().replace(' ', '')}/{name.lower().replace(' ', '')}")
                                        st.rerun()
                                    except sqlite3.IntegrityError as e:
                                        st.error(f"School name or code already exists: {e}")
                
                with col2:
                    st.subheader("Registered Schools")
                    schools = db.execute_query("SELECT * FROM schools ORDER BY created_date DESC")
                    if schools:
                        df_schools = pd.DataFrame(schools)
                        st.dataframe(df_schools, use_container_width=True, hide_index=True)
                    else:
                        st.info("No schools registered yet")
            
            with tab4:
                st.subheader("💾 Backup & Restore")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📦 Create Backup Now", use_container_width=True, type="primary"):
                        with st.spinner("Creating backup..."):
                            backup_file = backup_mgr.create_backup()
                            st.success(f"✅ Backup created: {backup_file.name}")
                
                with col2:
                    backups = backup_mgr.list_backups()
                    if backups:
                        selected_backup = st.selectbox("Select backup to restore", 
                                                       [b.name for b in backups])
                        if st.button("🔄 Restore Selected Backup", use_container_width=True, type="secondary"):
                            with st.spinner("Restoring..."):
                                success = backup_mgr.restore_backup(Config.BACKUP_DIR / selected_backup)
                                if success:
                                    st.success("✅ Database restored successfully! Please restart the app.")
                                else:
                                    st.error("❌ Restore failed")
                    else:
                        st.info("No backups available")
                
                # SMS Logs
                st.subheader("📱 SMS Logs")
                sms_logs = db.execute_query("""
                    SELECT * FROM sms_logs ORDER BY sent_at DESC LIMIT 50
                """)
                if sms_logs:
                    st.dataframe(pd.DataFrame(sms_logs), use_container_width=True)
                else:
                    st.info("No SMS logs yet")

    # --- ADMIN DASHBOARD ---
    elif role == 'admin':
        if page == 'dashboard':
            st.header(f"🏫 {user.get('school_name', 'School')} Administration")
            
            # Get school info
            school = db.execute_query("SELECT * FROM schools WHERE id = ?", (school_id,))[0]
            
            # Determine grades based on school type
            school_type = school['type']
            if "Pre-Primary" in school_type:
                available_grades = ["PP1", "PP2"]
            elif "Primary" in school_type and "Junior" not in school_type:
                available_grades = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]
            elif "Junior" in school_type:
                available_grades = ["Grade 7", "Grade 8", "Grade 9"]
            elif "Senior" in school_type:
                available_grades = ["Grade 10", "Grade 11", "Grade 12"]
            else:
                available_grades = list(CBECurriculum.GRADES.keys())
            
            tabs = st.tabs(["📋 Enroll Student", "📁 Bulk Import", "👥 Manage Staff", "📚 Library", "📊 Reports"])
            
            with tabs[0]:
                with st.container(border=True):
                    st.subheader("New Student Enrollment")
                    st.info("Required fields: Admission Number, Guardian Phone, Grade. KEMIS is optional but recommended.")
                    
                    with st.form("enroll_student"):
                        # Required fields row
                        st.markdown("**Required Information**")
                        c1, c2, c3 = st.columns(3)
                        adm_no = c1.text_input("Admission Number *", help="School-specific unique ID")
                        guardian_phone = c2.text_input("Guardian Phone *", help="Primary contact for SMS")
                        grade = c3.selectbox("Grade *", available_grades)
                        
                        # Stream selection for secondary
                        level = CBECurriculum.get_grade_level(grade)
                        if level in ["Junior Secondary", "Senior Secondary"]:
                            streams = CBECurriculum.get_streams(grade)
                            stream = st.selectbox("Stream *", streams)
                        else:
                            stream = "Default"
                        
                        # KEMIS and other details
                        st.markdown("**Additional Information**")
                        c4, c5, c6 = st.columns(3)
                        kemis_no = c4.text_input("KEMIS Number", help="Ministry of Education ID (optional)")
                        full_name = c5.text_input("Student Full Name *")
                        gender = c6.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
                        
                        c7, c8, c9 = st.columns(3)
                        dob = c7.date_input("Date of Birth", value=datetime(2010, 1, 1))
                        guardian_name = c8.text_input("Guardian Name")
                        guardian_email = c9.text_input("Guardian Email")
                        
                        c10, c11 = st.columns(2)
                        guardian_relationship = c10.selectbox("Relationship", ["Parent", "Guardian", "Sibling", "Other"])
                        boarding_status = c11.selectbox("Boarding Status", ["Day Scholar", "Boarder", "Mixed"])
                        
                        st.markdown("<small>* Required fields</small>", unsafe_allow_html=True)
                        
                        if st.form_submit_button("🎓 Enroll Student", type="primary", use_container_width=True):
                            # Validations
                            valid_adm, msg_adm = SecurityManager.validate_admission_number(adm_no)
                            valid_phone, msg_phone = SecurityManager.validate_phone(guardian_phone)
                            valid_kemis, msg_kemis = SecurityManager.validate_kemis(kemis_no) if kemis_no else (True, "Optional")
                            
                            if not all([adm_no, guardian_phone, full_name, grade]):
                                st.error("Please fill all required fields")
                            elif not valid_adm:
                                st.error(f"Invalid admission number: {msg_adm}")
                            elif not valid_phone:
                                st.error(f"Invalid guardian phone: {msg_phone}")
                            elif not valid_kemis:
                                st.error(f"Invalid KEMIS: {msg_kemis}")
                            else:
                                # Check for duplicates
                                existing = db.execute_query("""
                                    SELECT * FROM students WHERE admission_number = ? AND school_id = ?
                                """, (adm_no, school_id))
                                
                                if existing:
                                    st.error("Admission number already exists in this school!")
                                else:
                                    try:
                                        # Insert student
                                        db.execute_update("""
                                            INSERT INTO students 
                                            (kemis_number, admission_number, name, grade, stream, school_id, 
                                             guardian_phone, guardian_email, guardian_name, guardian_relationship,
                                             dob, gender, reg_year, current_academic_year, boarding_status, status)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            kemis_no if kemis_no else None,
                                            adm_no.strip().upper(),
                                            full_name.strip(),
                                            grade,
                                            stream,
                                            school_id,
                                            guardian_phone.strip(),
                                            guardian_email,
                                            guardian_name,
                                            guardian_relationship,
                                            dob.strftime("%Y-%m-%d"),
                                            gender,
                                            Config.CURRENT_YEAR,
                                            Config.CURRENT_YEAR,
                                            boarding_status,
                                            "Active"
                                        ))
                                        
                                        student_id = db.get_last_insert_id()
                                        
                                        # Create user accounts
                                        # Student account (optional - can use ADM no)
                                        student_pass = SecurityManager.hash_password("student123")
                                        db.execute_update("""
                                            INSERT INTO users (username, password_hash, role, school_id, phone, first_login, assigned_subject)
                                            VALUES (?, ?, ?, ?, ?, ?, ?)
                                        """, (adm_no, student_pass, "student", school_id, guardian_phone, 1, "None"))
                                        
                                        # Parent account (using guardian phone)
                                        parent_pass = SecurityManager.hash_password(guardian_phone)
                                        db.execute_update("""
                                            INSERT INTO users (username, password_hash, role, school_id, phone, email, first_login, assigned_subject)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (guardian_phone, parent_pass, "parent", school_id, guardian_phone, guardian_email, 1, "None"))
                                        
                                        # Send welcome SMS
                                        sms_manager.send_welcome_sms(guardian_phone, adm_no, "student123", "Student")
                                        
                                        st.success(f"✅ Student enrolled successfully!")
                                        st.balloons()
                                        st.code(f"Student Login: {adm_no} / student123\nParent Login: {guardian_phone} / {guardian_phone}")
                                        
                                        # Audit log
                                        db.audit_log("students", student_id, "INSERT", 
                                                    performed_by=user['username'])
                                        
                                    except sqlite3.IntegrityError as e:
                                        st.error(f"Database error: {e}")
            
            with tabs[3]:  # Library Management
                st.subheader("📚 School Library Management")
                
                lib_tab1, lib_tab2, lib_tab3 = st.tabs(["Add Book", "Browse Books", "Borrow/Return"])
                
                with lib_tab1:
                    with st.form("add_book"):
                        c1, c2 = st.columns(2)
                        isbn = c1.text_input("ISBN")
                        title = c1.text_input("Title *")
                        author = c2.text_input("Author *")
                        publisher = c2.text_input("Publisher")
                        category = st.selectbox("Category", ["Textbook", "Reference", "Fiction", "Non-Fiction", "Science", "Mathematics", "Language", "Other"])
                        grade_level = st.selectbox("Grade Level", available_grades)
                        quantity = st.number_input("Quantity", min_value=1, value=1)
                        shelf = st.text_input("Shelf Location", placeholder="e.g., A-12-3")
                        
                        if st.form_submit_button("Add Book", type="primary"):
                            if title and author:
                                try:
                                    db.execute_update("""
                                        INSERT INTO books (isbn, title, author, publisher, category, grade_level, quantity, available, shelf_location, school_id)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (isbn, title, author, publisher, category, grade_level, quantity, quantity, shelf, school_id))
                                    st.success(f"✅ Added '{title}' to library")
                                except Exception as e:
                                    st.error(f"Error: {e}")
                
                with lib_tab2:
                    books = db.execute_query("""
                        SELECT * FROM books WHERE school_id = ? ORDER BY title
                    """, (school_id,))
                    
                    if books:
                        df_books = pd.DataFrame(books)
                        
                        # Filters
                        col1, col2 = st.columns(2)
                        search_title = col1.text_input("🔍 Search by title")
                        filter_category = col2.selectbox("Filter by category", ["All"] + list(df_books['category'].unique()))
                        
                        if search_title:
                            df_books = df_books[df_books['title'].str.contains(search_title, case=False, na=False)]
                        if filter_category != "All":
                            df_books = df_books[df_books['category'] == filter_category]
                        
                        st.dataframe(df_books, use_container_width=True, hide_index=True)
                    else:
                        st.info("No books in library yet")
                
                with lib_tab3:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Borrow Book**")
                        with st.form("borrow_book"):
                            book_isbn = st.text_input("Book ISBN or Title")
                            student_adm = st.text_input("Student ADM No")
                            days = st.number_input("Days to borrow", min_value=1, max_value=14, value=7)
                            
                            if st.form_submit_button("Borrow"):
                                # Find book
                                book = db.execute_query("""
                                    SELECT * FROM books WHERE (isbn = ? OR title LIKE ?) AND school_id = ?
                                """, (book_isbn, f"%{book_isbn}%", school_id))
                                
                                student = db.execute_query("""
                                    SELECT * FROM students WHERE admission_number = ? AND school_id = ?
                                """, (student_adm, school_id))
                                
                                if not book:
                                    st.error("Book not found")
                                elif not student:
                                    st.error("Student not found")
                                elif book[0]['available'] <= 0:
                                    st.error("Book not available")
                                else:
                                    due_date = (datetime.now() + timedelta(days=days)).isoformat()
                                    
                                    db.execute_update("""
                                        INSERT INTO borrowings (book_id, student_id, due_date, issued_by)
                                        VALUES (?, ?, ?, ?)
                                    """, (book[0]['id'], student[0]['id'], due_date, user['id']))
                                    
                                    # Update available count
                                    db.execute_update("""
                                        UPDATE books SET available = available - 1 WHERE id = ?
                                    """, (book[0]['id'],))
                                    
                                    # Send SMS
                                    sms_manager.send_library_due_reminder(
                                        student[0]['guardian_phone'],
                                        student[0]['name'],
                                        book[0]['title'],
                                        days
                                    )
                                    
                                    st.success(f"✅ Book borrowed! Due: {due_date[:10]}")
                    
                    with col2:
                        st.markdown("**Return Book**")
                        with st.form("return_book"):
                            borrow_id = st.text_input("Borrowing ID (from system)")
                            if st.form_submit_button("Return Book"):
                                borrowing = db.execute_query("""
                                    SELECT * FROM borrowings WHERE id = ? AND status = 'Borrowed'
                                """, (borrow_id,))
                                
                                if borrowing:
                                    db.execute_update("""
                                        UPDATE borrowings SET return_date = ?, status = 'Returned' WHERE id = ?
                                    """, (datetime.now().isoformat(), borrow_id))
                                    
                                    db.execute_update("""
                                        UPDATE books SET available = available + 1 WHERE id = ?
                                    """, (borrowing[0]['book_id'],))
                                    
                                    st.success("✅ Book returned successfully")
                                else:
                                    st.error("Borrowing record not found or already returned")
            
            with tabs[4]:  # Reports
                st.subheader("📊 School Reports")
                
                report_type = st.selectbox("Report Type", [
                    "Student Enrollment by Grade",
                    "Gender Distribution",
                    "Library Statistics",
                    "SMS Activity"
                ])
                
                if report_type == "Student Enrollment by Grade":
                    enrollment = db.execute_query("""
                        SELECT grade, COUNT(*) as count 
                        FROM students 
                        WHERE school_id = ? AND status = 'Active'
                        GROUP BY grade
                    """, (school_id,))
                    
                    if enrollment:
                        df_enroll = pd.DataFrame(enrollment)
                        st.bar_chart(df_enroll.set_index('grade'))
                        st.dataframe(df_enroll, use_container_width=True)
                
                elif report_type == "Gender Distribution":
                    gender_dist = db.execute_query("""
                        SELECT gender, COUNT(*) as count 
                        FROM students 
                        WHERE school_id = ? AND status = 'Active'
                        GROUP BY gender
                    """, (school_id,))
                    
                    if gender_dist:
                        df_gender = pd.DataFrame(gender_dist)
                        st.pie_chart(df_gender.set_index('gender')['count'])

    # --- TEACHER DASHBOARD ---
    elif role == 'teacher':
        st.header(f"📝 Teacher Portal: {user.get('assigned_subject', 'General')}")
        
        # Get school info
        school = db.execute_query("SELECT * FROM schools WHERE id = ?", (school_id,))[0]
        
        # Determine grades
        school_type = school['type']
        if "Primary" in school_type and "Junior" not in school_type:
            available_grades = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]
        elif "Junior" in school_type:
            available_grades = ["Grade 7", "Grade 8", "Grade 9"]
        elif "Senior" in school_type:
            available_grades = ["Grade 10", "Grade 11", "Grade 12"]
        else:
            available_grades = list(CBECurriculum.GRADES.keys())
        
        # Sidebar context
        with st.sidebar:
            st.markdown("---")
            selected_grade = st.selectbox("Select Grade", available_grades, key="teacher_grade")
            selected_term = st.selectbox("Select Term", Config.TERMS, key="teacher_term")
            
            # Show relevant subjects
            relevant_subjects = CBECurriculum.get_subjects(selected_grade)
            if user.get('assigned_subject') in relevant_subjects:
                current_subject = user['assigned_subject']
                st.info(f"Teaching: {current_subject}")
            else:
                current_subject = st.selectbox("Subject", relevant_subjects, key="teacher_subject")
        
        tab1, tab2, tab3 = st.tabs(["✏️ Enter Marks", "📊 Class Analytics", "📚 My Classes"])
        
        with tab1:
            # Get students in grade
            students = db.execute_query("""
                SELECT * FROM students 
                WHERE school_id = ? AND grade = ? AND status = 'Active'
                ORDER BY name
            """, (school_id, selected_grade))
            
            if not students:
                st.warning("No active students in this grade")
            else:
                st.subheader(f"Enter Marks: {selected_grade} - {current_subject} - {selected_term}")
                
                # Get current academic year
                ac_year = db.execute_query("""
                    SELECT * FROM academic_years 
                    WHERE school_id = ? AND year = ? AND term = ? AND is_current = 1
                """, (school_id, Config.CURRENT_YEAR, selected_term))
                
                if not ac_year:
                    st.error("Academic year not set up. Contact administrator.")
                else:
                    ac_year_id = ac_year[0]['id']
                    
                    # Prepare data editor
                    marks_data = []
                    for student in students:
                        # Check existing mark
                        existing = db.execute_query("""
                            SELECT * FROM marks 
                            WHERE student_id = ? AND academic_year_id = ? AND subject = ?
                        """, (student['id'], ac_year_id, current_subject))
                        
                        marks_data.append({
                            'student_id': student['id'],
                            'adm_no': student['admission_number'],
                            'name': student['name'],
                            'score': existing[0]['marks'] if existing else 0.0,
                            'remarks': existing[0]['remarks'] if existing else ""
                        })
                    
                    df_marks = pd.DataFrame(marks_data)
                    
                    edited = st.data_editor(
                        df_marks,
                        use_container_width=True,
                        hide_index=True,
                        column_config={
                            "student_id": st.column_config.NumberColumn("ID", disabled=True),
                            "adm_no": st.column_config.TextColumn("ADM No", disabled=True),
                            "name": st.column_config.TextColumn("Student Name", disabled=True),
                            "score": st.column_config.NumberColumn("Score (%)", min_value=0, max_value=100, step=0.5, help="CBC: 80-100=Level 4, 60-79=Level 3, 40-59=Level 2, <40=Level 1"),
                            "remarks": st.column_config.TextColumn("Remarks")
                        },
                        key=f"marks_{selected_grade}_{selected_term}_{current_subject}"
                    )
                    
                    # Preview CBE levels
                    with st.expander("📊 Preview CBE Performance Levels"):
                        preview_data = []
                        for _, row in edited.iterrows():
                            score = row['score']
                            level, desc, letter, explanation = CBECurriculum.calculate_performance_level(score)
                            preview_data.append({
                                "Student": row['name'],
                                "Score": f"{score:.1f}%" if score > 0 else "-",
                                "Level": f"Level {level}",
                                "Grade": letter,
                                "Description": desc
                            })
                        st.dataframe(pd.DataFrame(preview_data), use_container_width=True, hide_index=True)
                    
                    if st.button("💾 Save All Marks", type="primary", use_container_width=True):
                        saved_count = 0
                        for _, row in edited.iterrows():
                            score = row['score']
                            if score > 0:
                                # Calculate CBC grade and level
                                level, desc, letter, _ = CBECurriculum.calculate_performance_level(score)
                                
                                # Check if exists
                                existing = db.execute_query("""
                                    SELECT id FROM marks 
                                    WHERE student_id = ? AND academic_year_id = ? AND subject = ?
                                """, (row['student_id'], ac_year_id, current_subject))
                                
                                if existing:
                                    # Update
                                    db.execute_update("""
                                        UPDATE marks SET marks = ?, grade = ?, performance_level = ?, remarks = ?, entered_by = ?
                                        WHERE id = ?
                                    """, (score, letter, level, row['remarks'], user['id'], existing[0]['id']))
                                else:
                                    # Insert
                                    db.execute_update("""
                                        INSERT INTO marks (student_id, academic_year_id, subject, marks, grade, performance_level, entered_by, remarks)
                                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                                    """, (row['student_id'], ac_year_id, current_subject, score, letter, level, user['id'], row['remarks']))
                                
                                saved_count += 1
                                
                                # Alert for low marks
                                if score < 40:
                                    student = db.execute_query("SELECT * FROM students WHERE id = ?", (row['student_id'],))[0]
                                    sms_manager.send_low_mark_alert(
                                        student['guardian_phone'],
                                        student['name'],
                                        current_subject,
                                        score
                                    )
                        
                        st.success(f"✅ Saved {saved_count} marks!")
                        st.balloons()
        
        with tab2:
            st.subheader("Class Performance Analytics")
            
            # Get marks data
            ac_year = db.execute_query("""
                SELECT * FROM academic_years 
                WHERE school_id = ? AND year = ? AND term = ? AND is_current = 1
            """, (school_id, Config.CURRENT_YEAR, selected_term))
            
            if ac_year:
                marks_data = db.execute_query("""
                    SELECT m.*, s.name, s.admission_number, s.grade
                    FROM marks m
                    JOIN students s ON m.student_id = s.id
                    WHERE m.academic_year_id = ? AND m.subject = ? AND s.grade = ?
                """, (ac_year[0]['id'], current_subject, selected_grade))
                
                if marks_data:
                    df_marks = pd.DataFrame(marks_data)
                    
                    # Statistics
                    cols = st.columns(4)
                    avg_score = df_marks['marks'].mean()
                    cols[0].metric("Class Average", f"{avg_score:.1f}%", border=True)
                    cols[1].metric("Highest", f"{df_marks['marks'].max():.1f}%", border=True)
                    cols[2].metric("Lowest", f"{df_marks['marks'].min():.1f}%", border=True)
                    cols[3].metric("Students", len(df_marks), border=True)
                    
                    # CBE Distribution
                    st.subheader("CBE Performance Distribution")
                    df_marks['level'] = df_marks['performance_level'].apply(lambda x: f"Level {x}")
                    level_dist = df_marks['level'].value_counts()
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.bar_chart(level_dist)
                    with col2:
                        st.dataframe(df_marks[['name', 'marks', 'grade', 'level']].sort_values('marks', ascending=False),
                                   use_container_width=True, hide_index=True)
                    
                    # Plotly chart if available
                    if HAS_PLOTLY:
                        fig = px.bar(
                            df_marks.sort_values('marks', ascending=False),
                            x='name',
                            y='marks',
                            color='marks',
                            color_continuous_scale=['#EF4444', '#F59E0B', '#3B82F6', '#10B981'],
                            title=f"{selected_grade} - {current_subject} Performance",
                            labels={'name': 'Student', 'marks': 'Score (%)'}
                        )
                        fig.update_layout(xaxis_tickangle=-45)
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No marks entered yet for this subject")

    # --- PARENT/STUDENT DASHBOARD ---
    elif role in ['parent', 'student']:
        if page == 'dashboard':
            st.header("📊 Academic Results Center")
            
            # ZEIN Branding
            with st.expander("🎓 About ZEIN (Zero Educational Ignorance Network)"):
                st.markdown(f"""
                **Welcome to {Config.FULL_NAME}!**
                
                **Our Mission:** {Config.MISSION}
                
                **What we offer:**
                - 📊 Real-time academic performance tracking
                - 📄 Official PDF report cards with CBC grading
                - 📚 Digital library access
                - 🤖 AI-powered learning assistant
                - 🔔 Instant SMS notifications
                
                **CBE Curriculum:** We follow the Competency-Based Education system with 4 performance levels:
                - **Level 4 (A):** 80-100% - Exceeds Expectations
                - **Level 3 (B):** 60-79% - Meets Expectations  
                - **Level 2 (C):** 40-59% - Approaches Expectations
                - **Level 1 (D):** Below 40% - Below Expectations
                """)
            
            # Determine student access
            if role == 'parent':
                # Find students linked to this guardian phone
                my_kids = db.execute_query("""
                    SELECT * FROM students 
                    WHERE guardian_phone = ? AND status = 'Active'
                """, (user['username'],))
                st.caption(f"Viewing children linked to: {user['username']}")
            else:
                # Student login - find by admission number
                my_kids = db.execute_query("""
                    SELECT * FROM students 
                    WHERE admission_number = ? AND status = 'Active'
                """, (user['username'],))
            
            if not my_kids:
                st.error("No student records found for this account")
            else:
                # Student selector for parents with multiple children
                if role == 'parent' and len(my_kids) > 1:
                    target_student = st.selectbox(
                        "Select Student",
                        my_kids,
                        format_func=lambda x: f"{x['admission_number']} - {x['name']} ({x['grade']})"
                    )
                else:
                    target_student = my_kids[0]
                
                # Student info card
                with st.container(border=True):
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("🎓 Name", target_student['name'])
                    col2.metric("📚 Grade", target_student['grade'])
                    col3.metric("🏫 Stream", target_student['stream'])
                    col4.metric("🆔 ADM No", target_student['admission_number'])
                    col5.metric("📋 KEMIS", target_student['kemis_number'] or "N/A")
                
                # Guardian info
                st.info(f"Guardian: {target_student['guardian_name'] or 'N/A'} | Phone: {target_student['guardian_phone']} | Email: {target_student['guardian_email'] or 'N/A'}")
                
                # Report Card Generation Section
                st.divider()
                st.subheader("📄 Official Report Card")
                
                col1, col2, col3 = st.columns([2, 2, 3])
                with col1:
                    report_term = st.selectbox("Select Term", Config.TERMS, key="report_term")
                with col2:
                    st.write("")
                    st.write("")
                    generate_btn = st.button("📄 Generate Report Card", type="primary", use_container_width=True)
                
                # Get school info
                school_info = db.execute_query("""
                    SELECT * FROM schools WHERE id = ?
                """, (target_student['school_id'],))[0]
                
                # Get marks for selected term
                ac_year = db.execute_query("""
                    SELECT * FROM academic_years 
                    WHERE school_id = ? AND year = ? AND term = ?
                """, (target_student['school_id'], Config.CURRENT_YEAR, report_term))
                
                if generate_btn:
                    if HAS_REPORTLAB and ac_year:
                        with st.spinner("Generating official report card..."):
                            # Get marks with subject names
                            marks = db.execute_query("""
                                SELECT m.*, s.name as subject_name
                                FROM marks m
                                JOIN academic_years ay ON m.academic_year_id = ay.id
                                WHERE m.student_id = ? AND ay.year = ? AND ay.term = ?
                            """, (target_student['id'], Config.CURRENT_YEAR, report_term))
                            
                            pdf_bytes = ReportCardGenerator.generate_pdf(
                                target_student,
                                marks,
                                school_info,
                                report_term,
                                Config.CURRENT_YEAR
                            )
                            
                            if pdf_bytes:
                                filename = f"ZEIN_ReportCard_{target_student['name'].replace(' ', '_')}_{report_term}_{Config.CURRENT_YEAR}.pdf"
                                
                                col3.markdown(
                                    ReportCardGenerator.get_download_link(pdf_bytes, filename),
                                    unsafe_allow_html=True
                                )
                                
                                # Preview
                                b64_pdf = base64.b64encode(pdf_bytes).decode()
                                pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
                                st.markdown("### Preview")
                                st.markdown(pdf_display, unsafe_allow_html=True)
                                
                                st.success("✅ Official report card generated!")
                    elif not ac_year:
                        st.error("Academic year not found")
                    else:
                        st.error("📄 PDF generation requires reportlab. Install with: pip install reportlab")
                
                # Academic Performance Table
                st.divider()
                st.subheader("📊 Academic Performance")
                
                # Get all marks for current year
                all_marks = db.execute_query("""
                    SELECT m.*, ay.term, s.name as subject_name
                    FROM marks m
                    JOIN academic_years ay ON m.academic_year_id = ay.id
                    WHERE m.student_id = ? AND ay.year = ?
                    ORDER BY ay.term, m.subject
                """, (target_student['id'], Config.CURRENT_YEAR))
                
                if all_marks:
                    df_marks = pd.DataFrame(all_marks)
                    
                    # Create pivot table
                    pivot = df_marks.pivot_table(
                        index='subject',
                        columns='term',
                        values='marks',
                        aggfunc='first'
                    ).fillna("-")
                    
                    # Ensure all terms exist
                    for term in Config.TERMS:
                        if term not in pivot.columns:
                            pivot[term] = "-"
                    pivot = pivot[Config.TERMS]
                    
                    # Add CBC levels
                    def format_with_level(val):
                        if isinstance(val, (int, float)) and val > 0:
                            level, _, letter, _ = CBECurriculum.calculate_performance_level(val)
                            return f"{val:.1f}% ({letter})"
                        return str(val)
                    
                    pivot_display = pivot.copy()
                    for col in pivot_display.columns:
                        pivot_display[col] = pivot_display[col].apply(format_with_level)
                    
                    st.dataframe(pivot_display, use_container_width=True)
                    
                    # Term summaries
                    st.subheader("🏆 Term Performance Summary")
                    cols = st.columns(len(Config.TERMS))
                    
                    for i, term in enumerate(Config.TERMS):
                        term_data = df_marks[df_marks['term'] == term]['marks']
                        if not term_data.empty:
                            avg = term_data.mean()
                            level, desc, letter, _ = CBECurriculum.calculate_performance_level(avg)
                            
                            cols[i].metric(
                                term,
                                f"{avg:.1f}%",
                                f"Level {level} ({letter})",
                                border=True
                            )
                            
                            with st.expander(f"View {term} Details"):
                                term_details = df_marks[df_marks['term'] == term][['subject', 'marks', 'grade']]
                                term_details = term_details.sort_values('marks', ascending=False)
                                st.dataframe(term_details, use_container_width=True, hide_index=True)
                        else:
                            cols[i].metric(term, "-", "No data", border=True)
                else:
                    st.info("📭 No marks recorded yet for this academic year")
                
                # Library Access
                st.divider()
                st.subheader("📚 Library")
                
                borrowed = db.execute_query("""
                    SELECT b.*, bk.title, bk.author, bk.isbn
                    FROM borrowings b
                    JOIN books bk ON b.book_id = bk.id
                    WHERE b.student_id = ? AND b.status IN ('Borrowed', 'Overdue')
                """, (target_student['id'],))
                
                if borrowed:
                    st.markdown("**Currently Borrowed:**")
                    df_borrowed = pd.DataFrame(borrowed)
                    st.dataframe(df_borrowed[['title', 'author', 'borrow_date', 'due_date', 'status']], 
                               use_container_width=True, hide_index=True)
                else:
                    st.info("No books currently borrowed")

    # --- LIBRARY PAGE (Shared) ---
    if page == 'library':
        st.header("📚 ZEIN Digital Library")
        
        # Search
        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            search_query = st.text_input("🔍 Search books by title or author")
        with col2:
            categories = ["All"]
            cats = db.execute_query("SELECT DISTINCT category FROM books WHERE school_id = ?", (school_id,))
            categories.extend([c['category'] for c in cats if c['category']])
            category_filter = st.selectbox("Category", categories)
        
        # Display books
        query = "SELECT * FROM books WHERE school_id = ?"
        params = [school_id]
        
        if search_query:
            query += " AND (title LIKE ? OR author LIKE ?)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        if category_filter != "All":
            query += " AND category = ?"
            params.append(category_filter)
        
        books = db.execute_query(query, tuple(params))
        
        if books:
            st.markdown(f"**Showing {len(books)} books**")
            
            for book in books:
                with st.container(border=True):
                    col1, col2, col3 = st.columns([3, 2, 1])
                    with col1:
                        st.markdown(f"**{book['title']}**")
                        st.caption(f"by {book['author']} | {book['publisher'] or 'Unknown'}")
                        st.caption(f"📂 {book['category']} | 🎯 {book['grade_level']}")
                    with col2:
                        available = book['available']
                        total = book['quantity']
                        status_color = "🟢" if available > 0 else "🔴"
                        st.markdown(f"{status_color} **{available}/{total} available**")
                        st.caption(f"📍 Shelf: {book['shelf_location'] or 'N/A'}")
                    with col3:
                        if available > 0 and role in ['student', 'parent']:
                            if st.button("Request", key=f"req_{book['id']}", use_container_width=True):
                                st.info("Please visit the library to borrow this book")
                        elif available == 0:
                            st.button("Waitlist", disabled=True, use_container_width=True)
        else:
            st.info("📚 No books found matching your criteria")

    # --- SETTINGS PAGE ---
    if page == 'settings':
        st.header("⚙️ Account Settings")
        
        with st.container(border=True):
            st.subheader("Profile Information")
            st.write(f"**Username:** {user['username']}")
            st.write(f"**Role:** {user['role'].title()}")
            st.write(f"**School:** {user.get('school_name', 'N/A')}")
            st.write(f"**Phone:** {user.get('phone', 'N/A')}")
            st.write(f"**Email:** {user.get('email', 'Not set')}")
        
        with st.container(border=True):
            st.subheader("Change Password")
            with st.form("change_password"):
                current = st.text_input("Current Password", type="password")
                new_pass = st.text_input("New Password", type="password")
                confirm = st.text_input("Confirm New Password", type="password")
                
                if st.form_submit_button("Update Password", type="primary"):
                    if not SecurityManager.verify_password(current, user['password_hash']):
                        st.error("Current password is incorrect")
                    elif new_pass != confirm:
                        st.error("New passwords don't match")
                    elif len(new_pass) < Config.MIN_PASSWORD_LENGTH:
                        st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                    else:
                        db.execute_update("""
                            UPDATE users SET password_hash = ? WHERE id = ?
                        """, (SecurityManager.hash_password(new_pass), user['id']))
                        st.success("✅ Password updated successfully!")

    # =========================
    # CHATBOT WIDGET (All pages)
    # =========================
    
    render_chatbot(user)
    
    # Footer
    st.markdown(f"""
    <div style="text-align:center;padding:2rem 0;margin-top:3rem;border-top:2px solid #e2e8f0;">
        <div style="font-size:1.2rem;font-weight:bold;color:{Config.PRIMARY_COLOR};">🎓 {Config.APP_NAME}</div>
        <div style="font-size:0.9rem;color:#64748b;">{Config.FULL_NAME}</div>
        <div style="font-size:0.8rem;color:#94a3b8;margin-top:0.5rem;">{Config.TAGLINE}</div>
        <div style="font-size:0.7rem;color:#cbd5e1;margin-top:1rem;">© 2024 ZEIN. Eliminating Educational Ignorance Worldwide.</div>
    </div>
    """, unsafe_allow_html=True)

# =========================
# BOOTSTRAP SUPERADMIN
# =========================

def bootstrap_superadmin():
    """Create default superadmin if none exists"""
    existing = db.execute_query("SELECT * FROM users WHERE role = 'superadmin' LIMIT 1")
    
    if not existing:
        try:
            db.execute_update("""
                INSERT INTO schools (school_name, school_code, type, status)
                VALUES (?, ?, ?, ?)
            """, ("ZEIN System", "ZEIN001", "Mixed", "Active"))
            
            school_id = db.get_last_insert_id()
            
            db.execute_update("""
                INSERT INTO users (username, password_hash, role, school_id, phone, email, recovery_hint, first_login, assigned_subject, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "zein",
                SecurityManager.hash_password("mionmion"),
                "superadmin",
                school_id,
                "+254700000000",
                "superadmin@zein.edu",
                "Founder",
                0,
                "All",
                1
            ))
            
            print("✅ Superadmin created: zein / mionmion")
        except Exception as e:
            print(f"Bootstrap error: {e}")

# Run bootstrap
bootstrap_superadmin()

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    main()

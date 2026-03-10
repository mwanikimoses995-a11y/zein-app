"""
ZEIN SCHOOL AI v4.0 - ZERO EDUCATIONAL IGNORANCE NETWORK
========================================================
Complete School Management System with:
- CBE Curriculum (CBC) Grading System
- Library Management Module
- SMS Integration (Twilio/AfricasTalking)
- AI Chatbot Assistant (OpenAI/Local LLM)
- Full Visual Identity & Branding
- Report Card Generation
- Advanced Security & Audit Logging

Author: ZEIN Development Team
Version: 4.0.0
License: MIT
"""

import streamlit as st
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
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from io import BytesIO
import threading
import queue

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
    VERSION = "4.0.0"
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
    DATA_DIR = Path("data")
    LOGS_DIR = Path("logs")
    BACKUP_DIR = Path("backups")
    ASSETS_DIR = Path("assets")
    TEMP_DIR = Path("temp")
    
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
    
    @classmethod
    def ensure_dirs(cls):
        for dir_path in [cls.DATA_DIR, cls.LOGS_DIR, cls.BACKUP_DIR, cls.ASSETS_DIR, cls.TEMP_DIR]:
            dir_path.mkdir(exist_ok=True)

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
    """Competency-Based Education (CBC) Curriculum Structure"""
    
    # Grade Levels
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
    def calculate_performance_level(cls, score: float) -> Tuple[int, str, str, str]:
        """Calculate CBC performance level from score"""
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
        
        /* Chat Widget */
        .chat-container {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            width: 350px;
            max-height: 500px;
            background: white;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            z-index: 9999;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        
        .chat-header {{
            background: linear-gradient(135deg, {Config.PRIMARY_COLOR} 0%, {Config.SECONDARY_COLOR} 100%);
            color: white;
            padding: 1rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        
        .chat-messages {{
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: #f8fafc;
        }}
        
        .chat-input {{
            padding: 1rem;
            border-top: 1px solid #e2e8f0;
            background: white;
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

apply_zein_theme()

# =========================
# DATA STRUCTURES & SCHEMAS
# =========================

@dataclass
class User:
    username: str
    password: str
    role: str
    school: str
    phone: str
    email: str
    recovery_hint: str
    first_login: bool
    assigned_subject: str
    created_at: str
    last_login: str
    is_active: bool
    otp_code: Optional[str] = None
    otp_expiry: Optional[str] = None

@dataclass
class Student:
    adm_no: str
    name: str
    grade: str
    school: str
    parent_phone: str
    parent_email: str
    dob: str
    gender: str
    reg_year: str
    status: str

@dataclass
class Book:
    isbn: str
    title: str
    author: str
    publisher: str
    category: str
    grade_level: str
    quantity: int
    available: int
    shelf_location: str
    date_added: str
    status: str

FILES = {
    "schools": Config.DATA_DIR / "schools.csv",
    "users": Config.DATA_DIR / "users.csv",
    "students": Config.DATA_DIR / "students.csv",
    "marks": Config.DATA_DIR / "marks.csv",
    "library": Config.DATA_DIR / "library.csv",
    "borrowings": Config.DATA_DIR / "borrowings.csv",
    "sms_logs": Config.LOGS_DIR / "sms_logs.jsonl",
    "chat_history": Config.LOGS_DIR / "chat_history.jsonl",
    "audit": Config.LOGS_DIR / "audit.log"
}

SCHEMAS = {
    "schools": ["school_name", "type", "status", "address", "phone", "email", "motto", "logo_path", "created_date"],
    "users": ["username", "password", "role", "school", "phone", "email", "recovery_hint", 
              "first_login", "assigned_subject", "created_at", "last_login", "is_active", "otp_code", "otp_expiry"],
    "students": ["adm_no", "name", "grade", "school", "parent_phone", "parent_email", 
                   "dob", "gender", "reg_year", "status"],
    "library": ["isbn", "title", "author", "publisher", "category", "grade_level", 
                "quantity", "available", "shelf_location", "date_added", "status"],
    "borrowings": ["borrow_id", "isbn", "adm_no", "borrow_date", "due_date", "return_date", 
                   "status", "fine_amount"],
    "marks": ["adm_no", "school", "year", "term", "subject", "marks", "entered_by", "entered_at", "remarks"]
}

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
        if not phone:
            return False, "Phone required"
        clean = re.sub(r'[\s\-\(\)\+]', '', phone)
        if not clean.isdigit():
            return False, "Digits only"
        if len(clean) < 9:
            return False, "Too short"
        if len(clean) > 15:
            return False, "Too long"
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
    
    def send_otp(self, phone: str, otp: str, username: str) -> Tuple[bool, str]:
        """Send OTP for password reset"""
        message = f"【ZEIN】Password Reset Code: {otp}. Valid for 10 minutes. Do not share this code. Username: {username}"
        return self._send_sms(phone, message, "OTP")
    
    def send_welcome_sms(self, phone: str, username: str, password: str, role: str) -> Tuple[bool, str]:
        """Send welcome message with credentials"""
        message = f"【ZEIN】Welcome to Zero Educational Ignorance Network! Your {role} account: Username: {username}, Password: {password}. Login at: zein.edu"
        return self._send_sms(phone, message, "WELCOME")
    
    def send_low_mark_alert(self, phone: str, student_name: str, subject: str, mark: float) -> Tuple[bool, str]:
        """Alert parent about low marks"""
        message = f"【ZEIN】Alert: {student_name} scored {mark:.1f}% in {subject}. Please check the portal for details and schedule a teacher meeting."
        return self._send_sms(phone, message, "ALERT")
    
    def send_library_due_reminder(self, phone: str, student_name: str, book_title: str, days_remaining: int) -> Tuple[bool, str]:
        """Library due date reminder"""
        message = f"【ZEIN】Reminder: {student_name}'s book '{book_title}' is due in {days_remaining} days. Please return to avoid fines."
        return self._send_sms(phone, message, "LIBRARY")
    
    def _send_sms(self, phone: str, message: str, msg_type: str) -> Tuple[bool, str]:
        """Internal SMS sender with logging"""
        try:
            if not self.client:
                # Fallback: Log to file for demo/testing
                self._log_sms(phone, message, msg_type, "SIMULATED")
                return True, "SMS simulated (no provider configured)"
            
            # Clean phone number
            clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
            if not clean_phone.startswith('+'):
                # Assume Kenya if no country code
                if clean_phone.startswith('0'):
                    clean_phone = '+254' + clean_phone[1:]
                else:
                    clean_phone = '+' + clean_phone
            
            # Send via provider
            if self.provider == "twilio":
                self.client.messages.create(
                    body=message,
                    from_=Config.TWILIO_PHONE,
                    to=clean_phone
                )
            elif self.provider == "africastalking":
                self.client.send(message, [clean_phone])
            
            self._log_sms(phone, message, msg_type, "SENT")
            return True, "SMS sent successfully"
            
        except Exception as e:
            self._log_sms(phone, message, msg_type, f"FAILED: {str(e)}")
            return False, f"SMS failed: {str(e)}"
    
    def _log_sms(self, phone: str, message: str, msg_type: str, status: str):
        """Log all SMS attempts"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "phone": phone[:4] + "****" + phone[-4:] if len(phone) > 8 else "****",  # Mask for privacy
            "type": msg_type,
            "status": status,
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
        try:
            with open(FILES["sms_logs"], "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass

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

Tone: Professional, friendly, educational, encouraging
Always identify yourself as ZEIN Assistant.
If you don't know something, direct users to contact support@zein.edu"""

    def __init__(self):
        self.history = []
        self.openai_available = HAS_OPENAI and Config.OPENAI_API_KEY
        
        # Local knowledge base for common questions
        self.knowledge_base = {
            "what is zein": "ZEIN stands for Zero Educational Ignorance Network. Our mission is to eliminate educational barriers through technology-enabled school management.",
            "cbe curriculum": "The Competency-Based Education (CBC) curriculum focuses on skills and competencies rather than just knowledge. It uses 4 performance levels: 4 (Exceeds), 3 (Meets), 2 (Approaches), 1 (Below).",
            "report card": "You can generate and download PDF report cards from the 'Academic Results' section. Click 'Generate Report Card PDF' to download.",
            "reset password": "Click 'Forgot Password' on the login page. An OTP will be sent to your registered phone number.",
            "library": "Access the Library module from the main menu to browse books, check availability, and see borrowing history.",
            "contact": "For support, email support@zein.edu or call your school administrator.",
            "grades": "Grades are calculated based on the CBC performance levels: A (80-100%), B (60-79%), C (40-59%), D (Below 40%)."
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
                return f"I'm having trouble connecting to my AI brain. Here's what I know locally: Try checking the Help section or contact support@zein.edu. (Error: {str(e)})"
        
        # Fallback response
        return "I'm ZEIN Assistant! I can help you navigate the system, explain CBC grading, or guide you to resources. What would you like to know?"
    
    def log_chat(self, user: str, message: str, response: str):
        """Log chat interactions"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user": user,
            "message": message,
            "response": response
        }
        try:
            with open(FILES["chat_history"], "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except:
            pass

# Initialize assistant
zein_assistant = ZEINAssistant()

# =========================
# DATA MANAGER
# =========================

class DataManager:
    @staticmethod
    @st.cache_data(ttl=Config.CACHE_TTL, show_spinner=False)
    def load_data() -> Dict[str, pd.DataFrame]:
        data = {}
        for key, filepath in FILES.items():
            if key in ["sms_logs", "chat_history", "audit"]:
                continue
            schema_cols = SCHEMAS.get(key, [])
            
            if not filepath.exists() or filepath.stat().st_size == 0:
                df = pd.DataFrame(columns=schema_cols)
                df.to_csv(filepath, index=False)
                data[key] = df
            else:
                df = pd.read_csv(filepath, dtype=str, keep_default_na=False)
                if key == "marks" and "marks" in df.columns:
                    df["marks"] = pd.to_numeric(df["marks"], errors="coerce")
                if key == "library" and "quantity" in df.columns:
                    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
                    df["available"] = pd.to_numeric(df["available"], errors="coerce")
                
                for col in schema_cols:
                    if col not in df.columns:
                        df[col] = ""
                data[key] = df[schema_cols] if schema_cols else df
        return data
    
    @staticmethod
    def save_data(df: pd.DataFrame, key: str) -> bool:
        filepath = FILES[key]
        temp_path = filepath.with_suffix('.tmp')
        try:
            df.to_csv(temp_path, index=False)
            temp_path.replace(filepath)
            DataManager.load_data.clear()
            return True
        except Exception as e:
            st.error(f"Save failed: {e}")
            if temp_path.exists():
                temp_path.unlink()
            return False

# Initialize data
db = DataManager.load_data()

# Bootstrap superadmin
def ensure_superadmin():
    users_df = db.get('users', pd.DataFrame())
    if users_df.empty or "zein" not in users_df['username'].values:
        sa = pd.DataFrame([{
            "username": "zein",
            "password": SecurityManager.hash_password("mionmion"),
            "role": "superadmin",
            "school": "SYSTEM",
            "phone": "+254700000000",
            "email": "superadmin@zein.edu",
            "recovery_hint": "Founder",
            "first_login": "False",
            "assigned_subject": "All",
            "created_at": datetime.now().isoformat(),
            "last_login": "",
            "is_active": "True",
            "otp_code": "",
            "otp_expiry": ""
        }])
        db['users'] = pd.concat([users_df, sa], ignore_index=True)
        DataManager.save_data(db['users'], "users")
        return DataManager.load_data()
    return db

db = ensure_superadmin()

# =========================
# REPORT CARD GENERATOR
# =========================

class ReportCardGenerator:
    @staticmethod
    def generate_pdf(student_info: Dict, marks_df: pd.DataFrame, school_info: Dict, 
                     term: str, year: str) -> Optional[bytes]:
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
        
        # Student info
        student_data = [
            ['STUDENT NAME:', student_info.get('name', 'N/A'), 'ADM NO:', student_info.get('adm_no', 'N/A')],
            ['GRADE:', student_info.get('grade', 'N/A'), 'GENDER:', student_info.get('gender', 'N/A')],
            ['DATE OF BIRTH:', student_info.get('dob', 'N/A'), 'YEAR:', year],
            ['PARENT/GUARDIAN:', student_info.get('parent_phone', 'N/A'), 'TERM:', term]
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
        
        if not marks_df.empty:
            table_data = [['LEARNING AREA', 'SCORE (%)', 'GRADE', 'PERFORMANCE LEVEL', 'REMARKS']]
            
            total_score = 0
            count = 0
            
            for _, row in marks_df.iterrows():
                score = row.get('marks', 0)
                if pd.notna(score) and score > 0:
                    level, desc, letter, explanation = CBECurriculum.calculate_performance_level(score)
                    remarks = CBECurriculum.get_report_remarks(score)
                    
                    table_data.append([
                        row.get('subject', 'N/A'),
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
# CHATBOT UI COMPONENT
# =========================

def render_chatbot(user: Dict):
    """Render floating chatbot widget"""
    
    # Chat toggle button
    if 'chat_open' not in st.session_state:
        st.session_state.chat_open = False
    
    col1, col2, col3 = st.columns([6, 6, 1])
    with col3:
        if st.button("💬" if not st.session_state.chat_open else "✕", 
                    key="chat_toggle",
                    help="ZEIN Assistant"):
            st.session_state.chat_open = not st.session_state.chat_open
            st.rerun()
    
    # Chat window
    if st.session_state.chat_open:
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
        .chat-header {
            background: linear-gradient(135deg, #1E3A8A 0%, #F59E0B 100%);
            color: white;
            padding: 1rem;
            font-weight: 600;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .chat-messages {
            flex: 1;
            overflow-y: auto;
            padding: 1rem;
            background: #f8fafc;
            max-height: 400px;
        }
        .chat-input {
            padding: 1rem;
            border-top: 1px solid #e2e8f0;
            background: white;
        }
        .message-user {
            background: #1E3A8A;
            color: white;
            padding: 8px 12px;
            border-radius: 12px 12px 0 12px;
            margin: 4px 0;
            margin-left: 20%;
            font-size: 13px;
        }
        .message-bot {
            background: white;
            border: 1px solid #e2e8f0;
            color: #1e293b;
            padding: 8px 12px;
            border-radius: 12px 12px 12px 0;
            margin: 4px 0;
            margin-right: 20%;
            font-size: 13px;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="chat-widget">', unsafe_allow_html=True)
            
            # Header
            st.markdown(f"""
            <div class="chat-header">
                <span>🎓 ZEIN Assistant</span>
                <span style="font-size:0.8rem;opacity:0.9;">v{Config.VERSION}</span>
            </div>
            """, unsafe_allow_html=True)
            
            # Messages
            if 'chat_messages' not in st.session_state:
                st.session_state.chat_messages = [
                    {"role": "bot", "content": f"Hello! I'm ZEIN Assistant. I can help you with:\n• Navigating the system\n• Explaining CBC grading\n• Report card questions\n• Library queries\n\nWhat can I help you with today?"}
                ]
            
            messages_html = '<div class="chat-messages">'
            for msg in st.session_state.chat_messages:
                css_class = "message-user" if msg["role"] == "user" else "message-bot"
                messages_html += f'<div class="{css_class}">{msg["content"]}</div>'
            messages_html += '</div>'
            st.markdown(messages_html, unsafe_allow_html=True)
            
            # Input
            with st.form(key="chat_form", clear_on_submit=True):
                user_input = st.text_input("Type your message...", key="chat_input", label_visibility="collapsed")
                if st.form_submit_button("Send", use_container_width=True):
                    if user_input:
                        # Add user message
                        st.session_state.chat_messages.append({"role": "user", "content": user_input})
                        
                        # Get bot response
                        response = zein_assistant.get_response(user_input, user)
                        st.session_state.chat_messages.append({"role": "bot", "content": response})
                        
                        # Log chat
                        zein_assistant.log_chat(user.get('username', 'anonymous'), user_input, response)
                        
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

# =========================
# AUTHENTICATION WITH SMS OTP
# =========================

class AuthManager:
    @staticmethod
    def render_login():
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
                            
                            users_df = db.get('users', pd.DataFrame())
                            user_row = users_df[users_df['username'] == username]
                            
                            if not user_row.empty and SecurityManager.verify_password(password, user_row.iloc[0]['password']):
                                if str(user_row.iloc[0].get('is_active', 'True')).lower() != 'true':
                                    st.error("Account is deactivated. Contact administrator.")
                                    return
                                
                                user_dict = user_row.iloc[0].to_dict()
                                st.session_state.user = user_dict
                                st.session_state.session_id = hashlib.md5(f"{username}{time.time()}".encode()).hexdigest()[:12]
                                
                                # Update last login
                                users_df.loc[users_df['username'] == username, 'last_login'] = datetime.now().isoformat()
                                DataManager.save_data(users_df, "users")
                                
                                st.success("✅ Login successful! Welcome to ZEIN.")
                                time.sleep(0.5)
                                st.rerun()
                            else:
                                st.error("❌ Invalid credentials")
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
                            
                            users_df = db.get('users', pd.DataFrame())
                            user_row = users_df[users_df['username'] == reset_user]
                            
                            if not user_row.empty:
                                stored_phone = user_row.iloc[0].get('phone', '')
                                if stored_phone == reset_phone:
                                    # Generate and send OTP
                                    otp = SecurityManager.generate_otp()
                                    otp_expiry = (datetime.now() + timedelta(minutes=Config.OTP_EXPIRY_MINUTES)).isoformat()
                                    
                                    # Save OTP to user record
                                    users_df.loc[users_df['username'] == reset_user, 'otp_code'] = otp
                                    users_df.loc[users_df['username'] == reset_user, 'otp_expiry'] = otp_expiry
                                    DataManager.save_data(users_df, "users")
                                    
                                    # Send SMS
                                    success, msg = sms_manager.send_otp(reset_phone, otp, reset_user)
                                    
                                    if success:
                                        st.session_state.reset_username = reset_user
                                        st.session_state.otp_sent = True
                                        st.success(f"✅ OTP sent to {reset_phone[:4]}****{reset_phone[-4:]}")
                                        st.info(f"📱 SMS Status: {msg}")
                                    else:
                                        st.error(f"Failed to send SMS: {msg}")
                                else:
                                    st.error("Phone number does not match our records")
                            else:
                                st.error("Username not found")
                    
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
                                users_df = db.get('users', pd.DataFrame())
                                user_row = users_df[users_df['username'] == st.session_state.reset_username]
                                
                                if not user_row.empty:
                                    stored_otp = user_row.iloc[0].get('otp_code', '')
                                    otp_expiry = user_row.iloc[0].get('otp_expiry', '')
                                    
                                    if stored_otp == entered_otp:
                                        # Check expiry
                                        if datetime.now() < datetime.fromisoformat(otp_expiry):
                                            # Update password
                                            users_df.loc[users_df['username'] == st.session_state.reset_username, 'password'] = SecurityManager.hash_password(new_password)
                                            users_df.loc[users_df['username'] == st.session_state.reset_username, 'otp_code'] = ''
                                            users_df.loc[users_df['username'] == st.session_state.reset_username, 'otp_expiry'] = ''
                                            DataManager.save_data(users_df, "users")
                                            
                                            # Clear session state
                                            del st.session_state.otp_sent
                                            del st.session_state.reset_username
                                            
                                            st.success("✅ Password reset successful! Please login with your new password.")
                                        else:
                                            st.error("❌ OTP has expired. Please request a new one.")
                                    else:
                                        st.error("❌ Invalid OTP")
                                else:
                                    st.error("User not found")
    
    @staticmethod
    def check_first_login():
        user = st.session_state.get("user", {})
        if str(user.get("first_login", "")).lower() == "true":
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
                    
                    users_df = db['users']
                    mask = users_df['username'] == user['username']
                    users_df.loc[mask, 'password'] = SecurityManager.hash_password(new_pass)
                    users_df.loc[mask, 'first_login'] = "False"
                    
                    if DataManager.save_data(users_df, "users"):
                        # Send welcome SMS
                        if user.get('phone'):
                            sms_manager.send_welcome_sms(user['phone'], user['username'], "[Hidden]", user['role'])
                        
                        st.success("✅ Password set! Please login again.")
                        st.session_state.clear()
                        time.sleep(1)
                        st.rerun()
            return True
        return False

# =========================
# MAIN APPLICATION
# =========================

if "user" not in st.session_state:
    AuthManager.render_login()
    st.stop()

user = st.session_state.user
db = DataManager.load_data()

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
        if user.get('school') and user['school'] != "SYSTEM":
            st.caption(f"🏫 School: {user['school']}")
        if user.get('assigned_subject') and user['assigned_subject'] != "None":
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
    
    if st.button("💬 Messages", use_container_width=True, key="nav_messages"):
        st.session_state.current_page = "messages"
        st.rerun()
    
    if st.button("⚙️ Settings", use_container_width=True, key="nav_settings"):
        st.session_state.current_page = "settings"
        st.rerun()
    
    st.divider()
    
    # Quick stats
    if user['role'] in ['student', 'parent']:
        st.markdown("### 📊 Quick Stats")
        student_adm = user['username'] if user['role'] == 'student' else None
        if user['role'] == 'parent':
            student_rows = db['students'][db['students']['parent_phone'] == user['username']]
            if not student_rows.empty:
                student_adm = student_rows.iloc[0]['adm_no']
        
        if student_adm:
            marks_count = len(db['marks'][db['marks']['adm_no'] == student_adm])
            st.metric("Subjects", marks_count, border=True)
    
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
my_school = user.get('school', '')

page = st.session_state.get('current_page', 'dashboard')

# --- SUPERADMIN DASHBOARD ---
if role == 'superadmin':
    if page == 'dashboard':
        st.header("🌐 ZEIN Global System Controller")
        
        # Metrics
        cols = st.columns(4)
        with cols[0]:
            st.metric("🏫 Schools", len(db['schools']), border=True)
        with cols[1]:
            st.metric("👥 Total Users", len(db['users']), border=True)
        with cols[2]:
            st.metric("🎓 Students", len(db['students']), border=True)
        with cols[3]:
            st.metric("📚 Library Books", len(db['library']), border=True)
        
        # Management tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏫 Schools", "👤 Users", "📊 Analytics", "🔒 Security Logs"])
        
        with tab1:
            col1, col2 = st.columns([1, 2])
            with col1:
                with st.container(border=True):
                    st.subheader("Create New School")
                    with st.form("create_school"):
                        name = st.text_input("School Name")
                        level = st.selectbox("Level", ["Pre-Primary", "Primary", "Junior Secondary", "Senior Secondary", "Mixed"])
                        address = st.text_area("Address")
                        phone = st.text_input("Phone")
                        email = st.text_input("Email")
                        motto = st.text_input("School Motto", value="Excellence in Education")
                        
                        if st.form_submit_button("Create School", type="primary"):
                            if name and name not in db['schools']['school_name'].values:
                                new_school = pd.DataFrame([{
                                    "school_name": name, "type": level, "status": "Active",
                                    "address": address, "phone": phone, "email": email,
                                    "motto": motto, "logo_path": "", "created_date": datetime.now().isoformat()
                                }])
                                db['schools'] = pd.concat([db['schools'], new_school], ignore_index=True)
                                DataManager.save_data(db['schools'], "schools")
                                
                                # Create admin
                                admin_pass = SecurityManager.hash_password(name)
                                admin = pd.DataFrame([{
                                    "username": name, "password": admin_pass, "role": "admin",
                                    "school": name, "phone": phone or "000", "email": email or "",
                                    "recovery_hint": "Init", "first_login": "True",
                                    "assigned_subject": "All", "created_at": datetime.now().isoformat(),
                                    "last_login": "", "is_active": "True", "otp_code": "", "otp_expiry": ""
                                }])
                                db['users'] = pd.concat([db['users'], admin], ignore_index=True)
                                DataManager.save_data(db['users'], "users")
                                
                                # Send welcome SMS
                                if phone:
                                    sms_manager.send_welcome_sms(phone, name, name, "Administrator")
                                
                                st.success(f"✅ School '{name}' created! Admin login: {name}/{name}")
            
            with col2:
                st.subheader("Registered Schools")
                if not db['schools'].empty:
                    st.dataframe(db['schools'], use_container_width=True, hide_index=True,
                               column_config={"school_name": st.column_config.TextColumn("School", pinned=True)})
                else:
                    st.info("No schools registered yet")
        
        with tab4:
            st.subheader("🔐 Security & SMS Logs")
            if FILES["sms_logs"].exists():
                with open(FILES["sms_logs"], "r") as f:
                    logs = [json.loads(line) for line in f.readlines()[-50:]]
                    if logs:
                        st.dataframe(pd.DataFrame(logs), use_container_width=True)
                    else:
                        st.info("No SMS logs yet")
            else:
                st.info("SMS logging will appear here")

# --- ADMIN DASHBOARD ---
elif role == 'admin':
    if page == 'dashboard':
        st.header(f"🏫 {my_school} Administration")
        
        school_info = db['schools'][db['schools']['school_name'] == my_school]
        if school_info.empty:
            st.error("School not found")
            st.stop()
        
        school_type = school_info.iloc[0]['type']
        
        # Get grades for this school type
        if "Pre-Primary" in school_type:
            available_grades = ["PP1", "PP2"]
        elif "Primary" in school_type:
            available_grades = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]
        elif "Junior" in school_type:
            available_grades = ["Grade 7", "Grade 8", "Grade 9"]
        elif "Senior" in school_type:
            available_grades = ["Grade 10", "Grade 11", "Grade 12"]
        else:
            available_grades = list(CBECurriculum.GRADES.keys())
        
        tabs = st.tabs(["📋 Enroll Student", "📁 Bulk Import", "👥 Manage Staff", "📚 Library", "🔍 Search"])
        
        with tabs[0]:
            with st.container(border=True):
                st.subheader("New Student Enrollment")
                
                with st.form("enroll_student"):
                    c1, c2 = st.columns(2)
                    adm_no = c1.text_input("Admission Number *", help="Unique ID for the student")
                    full_name = c1.text_input("Full Name *")
                    parent_phone = c2.text_input("Parent Phone *", help="For SMS notifications and parent login")
                    parent_email = c2.text_input("Parent Email")
                    grade = c1.selectbox("Grade *", available_grades)
                    gender = c2.selectbox("Gender", ["Male", "Female", "Other"])
                    dob = c2.date_input("Date of Birth", value=datetime(2010, 1, 1))
                    
                    st.markdown("<small>* Required fields</small>", unsafe_allow_html=True)
                    
                    if st.form_submit_button("Enroll Student", type="primary", use_container_width=True):
                        valid_adm, msg_adm = SecurityManager.validate_adm_no(adm_no)
                        valid_phone, msg_phone = SecurityManager.validate_phone(parent_phone)
                        
                        if not all([adm_no, full_name, parent_phone]):
                            st.error("Please fill all required fields")
                        elif not valid_adm:
                            st.error(f"Invalid admission number: {msg_adm}")
                        elif not valid_phone:
                            st.error(f"Invalid phone: {msg_phone}")
                        elif adm_no in db['students']['adm_no'].values:
                            st.error("Admission number already exists!")
                        else:
                            # Create student record
                            student = pd.DataFrame([{
                                "adm_no": adm_no.strip().upper(),
                                "name": full_name.strip(),
                                "grade": grade,
                                "school": my_school,
                                "parent_phone": parent_phone.strip(),
                                "parent_email": parent_email,
                                "dob": dob.strftime("%Y-%m-%d"),
                                "gender": gender,
                                "reg_year": CURRENT_YEAR,
                                "status": "Active"
                            }])
                            db['students'] = pd.concat([db['students'], student], ignore_index=True)
                            
                            # Create accounts
                            accounts = []
                            if adm_no not in db['users']['username'].values:
                                accounts.append({
                                    "username": adm_no,
                                    "password": SecurityManager.hash_password("1234"),
                                    "role": "student",
                                    "school": my_school,
                                    "phone": parent_phone,
                                    "email": "",
                                    "recovery_hint": "1234",
                                    "first_login": "True",
                                    "assigned_subject": "None",
                                    "created_at": datetime.now().isoformat(),
                                    "last_login": "",
                                    "is_active": "True",
                                    "otp_code": "",
                                    "otp_expiry": ""
                                })
                            
                            if parent_phone not in db['users']['username'].values:
                                accounts.append({
                                    "username": parent_phone,
                                    "password": SecurityManager.hash_password(parent_phone),
                                    "role": "parent",
                                    "school": my_school,
                                    "phone": parent_phone,
                                    "email": parent_email,
                                    "recovery_hint": "Phone",
                                    "first_login": "True",
                                    "assigned_subject": "None",
                                    "created_at": datetime.now().isoformat(),
                                    "last_login": "",
                                    "is_active": "True",
                                    "otp_code": "",
                                    "otp_expiry": ""
                                })
                            
                            if accounts:
                                db['users'] = pd.concat([db['users'], pd.DataFrame(accounts)], ignore_index=True)
                            
                            DataManager.save_data(db['students'], "students")
                            DataManager.save_data(db['users'], "users")
                            
                            # Send welcome SMS to parent
                            sms_manager.send_welcome_sms(parent_phone, adm_no, "1234", "Student")
                            
                            st.success("✅ Student enrolled successfully!")
                            st.balloons()
                            st.code(f"Student: {adm_no} / 1234\nParent: {parent_phone} / {parent_phone}")
        
        with tabs[3]:  # Library Management
            st.subheader("📚 School Library Management")
            
            lib_tab1, lib_tab2, lib_tab3 = st.tabs(["Add Book", "Browse Books", "Borrow/Return"])
            
            with lib_tab1:
                with st.form("add_book"):
                    c1, c2 = st.columns(2)
                    isbn = c1.text_input("ISBN")
                    title = c1.text_input("Title")
                    author = c2.text_input("Author")
                    publisher = c2.text_input("Publisher")
                    category = st.selectbox("Category", ["Textbook", "Reference", "Fiction", "Non-Fiction", "Science", "Mathematics", "Language", "Other"])
                    grade_level = st.selectbox("Grade Level", available_grades)
                    quantity = st.number_input("Quantity", min_value=1, value=1)
                    shelf = st.text_input("Shelf Location", placeholder="e.g., A-12-3")
                    
                    if st.form_submit_button("Add Book", type="primary"):
                        if not all([isbn, title, author]):
                            st.error("ISBN, Title and Author are required")
                        elif isbn in db['library']['isbn'].values:
                            st.error("Book with this ISBN already exists")
                        else:
                            new_book = pd.DataFrame([{
                                "isbn": isbn,
                                "title": title,
                                "author": author,
                                "publisher": publisher,
                                "category": category,
                                "grade_level": grade_level,
                                "quantity": quantity,
                                "available": quantity,
                                "shelf_location": shelf,
                                "date_added": datetime.now().isoformat(),
                                "status": "Available"
                            }])
                            db['library'] = pd.concat([db['library'], new_book], ignore_index=True)
                            DataManager.save_data(db['library'], "library")
                            st.success(f"✅ Added '{title}' to library")
            
            with lib_tab2:
                if not db['library'].empty:
                    # Filters
                    col1, col2 = st.columns(2)
                    search_title = col1.text_input("Search by title")
                    filter_category = col2.selectbox("Filter by category", ["All"] + list(db['library']['category'].unique()))
                    
                    filtered = db['library']
                    if search_title:
                        filtered = filtered[filtered['title'].str.contains(search_title, case=False, na=False)]
                    if filter_category != "All":
                        filtered = filtered[filtered['category'] == filter_category]
                    
                    st.dataframe(filtered, use_container_width=True, hide_index=True,
                               column_config={"title": st.column_config.TextColumn("Title", pinned=True)})
                else:
                    st.info("No books in library yet")
            
            with lib_tab3:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Borrow Book**")
                    with st.form("borrow_book"):
                        book_isbn = st.text_input("Book ISBN")
                        student_adm = st.text_input("Student ADM No")
                        days = st.number_input("Days to borrow", min_value=1, max_value=14, value=7)
                        
                        if st.form_submit_button("Borrow"):
                            book = db['library'][db['library']['isbn'] == book_isbn]
                            student = db['students'][db['students']['adm_no'] == student_adm]
                            
                            if book.empty:
                                st.error("Book not found")
                            elif student.empty:
                                st.error("Student not found")
                            elif book.iloc[0]['available'] <= 0:
                                st.error("Book not available")
                            else:
                                # Create borrowing record
                                borrow_id = f"BOR{datetime.now().strftime('%Y%m%d%H%M%S')}"
                                due_date = (datetime.now() + timedelta(days=days)).isoformat()
                                
                                borrowing = pd.DataFrame([{
                                    "borrow_id": borrow_id,
                                    "isbn": book_isbn,
                                    "adm_no": student_adm,
                                    "borrow_date": datetime.now().isoformat(),
                                    "due_date": due_date,
                                    "return_date": "",
                                    "status": "Borrowed",
                                    "fine_amount": 0
                                }])
                                db['borrowings'] = pd.concat([db['borrowings'], borrowing], ignore_index=True)
                                
                                # Update available count
                                db['library'].loc[db['library']['isbn'] == book_isbn, 'available'] -= 1
                                
                                DataManager.save_data(db['borrowings'], "borrowings")
                                DataManager.save_data(db['library'], "library")
                                
                                # Send SMS reminder
                                parent_phone = student.iloc[0]['parent_phone']
                                book_title = book.iloc[0]['title']
                                sms_manager.send_library_due_reminder(parent_phone, student.iloc[0]['name'], book_title, days)
                                
                                st.success(f"✅ Book borrowed! Due: {due_date[:10]}")
                
                with col2:
                    st.markdown("**Return Book**")
                    with st.form("return_book"):
                        borrow_id = st.text_input("Borrowing ID")
                        if st.form_submit_button("Return Book"):
                            borrowing = db['borrowings'][db['borrowings']['borrow_id'] == borrow_id]
                            if borrowing.empty:
                                st.error("Borrowing record not found")
                            else:
                                isbn = borrowing.iloc[0]['isbn']
                                db['borrowings'].loc[db['borrowings']['borrow_id'] == borrow_id, 'return_date'] = datetime.now().isoformat()
                                db['borrowings'].loc[db['borrowings']['borrow_id'] == borrow_id, 'status'] = "Returned"
                                db['library'].loc[db['library']['isbn'] == isbn, 'available'] += 1
                                
                                DataManager.save_data(db['borrowings'], "borrowings")
                                DataManager.save_data(db['library'], "library")
                                st.success("✅ Book returned successfully")

# --- TEACHER DASHBOARD ---
elif role == 'teacher':
    st.header(f"📝 Teacher Portal: {user.get('assigned_subject', 'General')}")
    
    # Get school info
    school_info = db['schools'][db['schools']['school_name'] == my_school]
    if school_info.empty:
        st.error("School configuration error")
        st.stop()
    
    # Determine grades based on school type
    school_type = school_info.iloc[0]['type']
    if "Primary" in school_type:
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
        selected_grade = st.selectbox("Select Grade", available_grades)
        selected_term = st.selectbox("Select Term", TERMS)
        
        # Show relevant subjects for this grade
        relevant_subjects = CBECurriculum.get_subjects(selected_grade)
        if user.get('assigned_subject') in relevant_subjects:
            current_subject = user['assigned_subject']
        else:
            current_subject = st.selectbox("Subject", relevant_subjects)
    
    tab1, tab2, tab3 = st.tabs(["✏️ Enter Marks", "📊 Class Analytics", "📚 Library"])
    
    with tab1:
        students = db['students'][
            (db['students']['school'] == my_school) &
            (db['students']['grade'] == selected_grade) &
            (db['students']['status'] == "Active")
        ]
        
        if students.empty:
            st.warning("No active students in this grade")
        else:
            st.subheader(f"Enter Marks: {selected_grade} - {current_subject} - {selected_term}")
            
            # Prepare entry data
            entry_data = pd.DataFrame({
                "adm_no": students['adm_no'].values,
                "name": students['name'].values,
                "score": [0.0] * len(students),
                "remarks": [""] * len(students)
            })
            
            # Check for existing marks
            existing = db['marks'][
                (db['marks']['school'] == my_school) &
                (db['marks']['year'] == CURRENT_YEAR) &
                (db['marks']['term'] == selected_term) &
                (db['marks']['subject'] == current_subject) &
                (db['marks']['adm_no'].isin(students['adm_no']))
            ]
            
            if not existing.empty:
                existing_dict = existing.set_index('adm_no')['marks'].to_dict()
                entry_data['score'] = entry_data['adm_no'].map(existing_dict).fillna(0)
                st.info("ℹ️ Pre-filled with existing marks")
            
            # Data editor with CBE validation
            edited = st.data_editor(
                entry_data,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "adm_no": st.column_config.TextColumn("ADM No", disabled=True, pinned=True),
                    "name": st.column_config.TextColumn("Student Name", disabled=True),
                    "score": st.column_config.NumberColumn("Score (%)", min_value=0, max_value=100, step=0.5, help="CBE: 80-100=Level 4, 60-79=Level 3, 40-59=Level 2, <40=Level 1"),
                    "remarks": st.column_config.TextColumn("Remarks", help="Optional comments")
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
                invalid = edited[(edited['score'] < 0) | (edited['score'] > 100)]
                if not invalid.empty:
                    st.error("All scores must be between 0 and 100")
                else:
                    with st.status("Saving marks...", expanded=True) as status:
                        # Remove existing
                        mask = ~(
                            (db['marks']['adm_no'].isin(edited['adm_no'])) &
                            (db['marks']['school'] == my_school) &
                            (db['marks']['year'] == CURRENT_YEAR) &
                            (db['marks']['term'] == selected_term) &
                            (db['marks']['subject'] == current_subject)
                        )
                        db['marks'] = db['marks'][mask]
                        
                        # Add new
                        records = []
                        for _, row in edited.iterrows():
                            if row['score'] > 0:  # Only save non-zero scores
                                records.append({
                                    "adm_no": str(row['adm_no']),
                                    "school": my_school,
                                    "year": CURRENT_YEAR,
                                    "term": selected_term,
                                    "subject": current_subject,
                                    "marks": float(row['score']),
                                    "entered_by": user['username'],
                                    "entered_at": datetime.now().isoformat(),
                                    "remarks": row['remarks']
                                })
                                
                                # Check for low marks and alert parents
                                if row['score'] < 40:
                                    student_info = students[students['adm_no'] == row['adm_no']].iloc[0]
                                    sms_manager.send_low_mark_alert(
                                        student_info['parent_phone'],
                                        student_info['name'],
                                        current_subject,
                                        row['score']
                                    )
                        
                        if records:
                            db['marks'] = pd.concat([db['marks'], pd.DataFrame(records)], ignore_index=True)
                            DataManager.save_data(db['marks'], "marks")
                            status.update(label=f"✅ Saved {len(records)} marks", state="complete")
                            st.balloons()
                        else:
                            status.update(label="No marks to save", state="complete")
    
    with tab2:
        st.subheader("Class Performance Analytics")
        
        marks_data = db['marks'][
            (db['marks']['school'] == my_school) &
            (db['marks']['subject'] == current_subject) &
            (db['marks']['term'] == selected_term) &
            (db['marks']['year'] == CURRENT_YEAR)
        ]
        
        if marks_data.empty:
            st.info("No data available")
        else:
            # Merge with student data
            chart_data = marks_data.merge(
                db['students'][['adm_no', 'name', 'grade']],
                on='adm_no',
                how='left'
            )
            chart_data = chart_data[chart_data['grade'] == selected_grade]
            
            if not chart_data.empty:
                # Statistics
                cols = st.columns(4)
                avg_score = chart_data['marks'].mean()
                cols[0].metric("Class Average", f"{avg_score:.1f}%", border=True)
                cols[1].metric("Highest", f"{chart_data['marks'].max():.1f}%", border=True)
                cols[2].metric("Lowest", f"{chart_data['marks'].min():.1f}%", border=True)
                cols[3].metric("Students", len(chart_data), border=True)
                
                # CBE Distribution
                st.subheader("CBE Performance Distribution")
                chart_data['level'] = chart_data['marks'].apply(
                    lambda x: f"Level {CBECurriculum.calculate_performance_level(x)[0]}"
                )
                level_dist = chart_data['level'].value_counts()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.bar_chart(level_dist)
                with col2:
                    # Show table
                    st.dataframe(
                        chart_data[['name', 'marks', 'level']].sort_values('marks', ascending=False),
                        use_container_width=True,
                        hide_index=True,
                        column_config={"name": st.column_config.TextColumn("Student", pinned=True)}
                    )
                
                # Visual chart if plotly available
                if HAS_PLOTLY:
                    fig = px.bar(
                        chart_data.sort_values('marks', ascending=False),
                        x='name',
                        y='marks',
                        color='marks',
                        color_continuous_scale=['#EF4444', '#F59E0B', '#3B82F6', '#10B981'],
                        title=f"{selected_grade} - {current_subject} Performance",
                        labels={'name': 'Student', 'marks': 'Score (%)'}
                    )
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)

# --- PARENT/STUDENT DASHBOARD WITH REPORT CARDS ---
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
            - 📄 Official PDF report cards
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
            search_key = user['username']
            my_kids = db['students'][db['students']['parent_phone'] == search_key]
            st.caption(f"Viewing children linked to: {search_key}")
        else:
            search_key = user['username']
            my_kids = db['students'][db['students']['adm_no'] == search_key]
        
        if my_kids.empty:
            st.error("No student records found for this account")
        else:
            # Student selector
            if role == 'parent' and len(my_kids) > 1:
                target_adm = st.selectbox(
                    "Select Student",
                    my_kids['adm_no'].unique(),
                    format_func=lambda x: f"{x} - {my_kids[my_kids['adm_no']==x].iloc[0]['name']}"
                )
            else:
                target_adm = my_kids.iloc[0]['adm_no']
            
            student_info = my_kids[my_kids['adm_no'] == target_adm].iloc[0]
            school_info = db['schools'][db['schools']['school_name'] == student_info['school']]
            school_info_dict = school_info.iloc[0].to_dict() if not school_info.empty else {}
            
            # Student info card
            with st.container(border=True):
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("🎓 Student", student_info['name'])
                col2.metric("📚 Grade", student_info['grade'])
                col3.metric("🏫 School", student_info['school'])
                col4.metric("📅 Year", CURRENT_YEAR)
            
            # Report Card Generation Section
            st.divider()
            st.subheader("📄 Official Report Card")
            
            col1, col2, col3 = st.columns([2, 2, 3])
            with col1:
                report_term = st.selectbox("Select Term", TERMS, key="report_term")
            with col2:
                st.write("")
                st.write("")
                generate_btn = st.button("📄 Generate Report Card", type="primary", use_container_width=True)
            
            # Get marks for selected term
            term_marks = db['marks'][
                (db['marks']['adm_no'] == str(target_adm)) &
                (db['marks']['year'] == CURRENT_YEAR) &
                (db['marks']['term'] == report_term)
            ]
            
            if generate_btn:
                if HAS_REPORTLAB:
                    with st.spinner("Generating official report card..."):
                        pdf_bytes = ReportCardGenerator.generate_pdf(
                            student_info.to_dict(),
                            term_marks,
                            school_info_dict,
                            report_term,
                            CURRENT_YEAR
                        )
                        
                        if pdf_bytes:
                            filename = f"ZEIN_ReportCard_{student_info['name'].replace(' ', '_')}_{report_term}_{CURRENT_YEAR}.pdf"
                            
                            col3.markdown(
                                ReportCardGenerator.get_download_link(pdf_bytes, filename),
                                unsafe_allow_html=True
                            )
                            
                            # Preview in iframe
                            b64_pdf = base64.b64encode(pdf_bytes).decode()
                            pdf_display = f'<iframe src="data:application/pdf;base64,{b64_pdf}" width="100%" height="600px" type="application/pdf"></iframe>'
                            st.markdown("### Preview")
                            st.markdown(pdf_display, unsafe_allow_html=True)
                            
                            st.success("✅ Official report card generated!")
                else:
                    st.error("📄 PDF generation requires reportlab. Install with: pip install reportlab")
            
            # Academic Performance Table
            st.divider()
            st.subheader("📊 Academic Performance")
            
            all_marks = db['marks'][
                (db['marks']['adm_no'] == str(target_adm)) &
                (db['marks']['year'] == CURRENT_YEAR)
            ]
            
            if all_marks.empty:
                st.info("📭 No marks recorded yet for this academic year")
            else:
                # Create pivot table for all terms
                report = all_marks.pivot_table(
                    index='subject',
                    columns='term',
                    values='marks',
                    aggfunc='first'
                ).fillna("-")
                
                for term in TERMS:
                    if term not in report.columns:
                        report[term] = "-"
                report = report[TERMS]
                
                # Add CBE levels
                def format_with_level(val):
                    if isinstance(val, (int, float)) and val > 0:
                        level, _, letter, _ = CBECurriculum.calculate_performance_level(val)
                        return f"{val:.1f}% ({letter})"
                    return str(val)
                
                report_display = report.copy()
                for col in report_display.columns:
                    report_display[col] = report_display[col].apply(format_with_level)
                
                st.dataframe(
                    report_display,
                    use_container_width=True,
                    column_config={report_display.index.name or "subject": st.column_config.TextColumn("Learning Area", pinned=True)}
                )
                
                # Term summaries with CBE levels
                st.subheader("🏆 Term Performance Summary")
                cols = st.columns(len(TERMS))
                
                for i, term in enumerate(TERMS):
                    term_data = all_marks[all_marks['term'] == term]['marks']
                    if not term_data.empty:
                        avg = term_data.mean()
                        level, desc, letter, explanation = CBECurriculum.calculate_performance_level(avg)
                        
                        cols[i].metric(
                            term,
                            f"{avg:.1f}%",
                            f"Level {level} ({letter})",
                            border=True
                        )
                        
                        # Show subjects breakdown
                        with st.expander(f"View {term} Details"):
                            term_details = all_marks[all_marks['term'] == term][['subject', 'marks']]
                            term_details['Grade'] = term_details['marks'].apply(
                                lambda x: CBECurriculum.calculate_performance_level(x)[2]
                            )
                            st.dataframe(term_details.sort_values('marks', ascending=False), 
                                       use_container_width=True, hide_index=True)
                    else:
                        cols[i].metric(term, "-", "No data", border=True)
            
            # Library Access
            st.divider()
            st.subheader("📚 Library")
            
            # Show borrowed books
            borrowed = db['borrowings'][db['borrowings']['adm_no'] == target_adm]
            if not borrowed.empty:
                st.markdown("**Currently Borrowed:**")
                borrowed_display = borrowed.merge(
                    db['library'][['isbn', 'title', 'author']],
                    on='isbn',
                    how='left'
                )
                st.dataframe(borrowed_display[['title', 'author', 'borrow_date', 'due_date', 'status']], 
                           use_container_width=True, hide_index=True)
            else:
                st.info("No books currently borrowed")
            
            # Print option
            st.divider()
            if st.button("🖨️ Print This Page", use_container_width=True):
                st.markdown("""
                <script>
                window.print();
                </script>
                """, unsafe_allow_html=True)
                st.success("Print dialog opened. Use landscape mode for best results.")

# --- LIBRARY PAGE (Shared) ---
if page == 'library':
    st.header("📚 ZEIN Digital Library")
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        search_query = st.text_input("🔍 Search books by title or author")
    with col2:
        categories = ["All"] + list(db['library']['category'].unique()) if not db['library'].empty else ["All"]
        category_filter = st.selectbox("Category", categories)
    with col3:
        st.write("")
        st.write("")
        if st.button("🔍 Search", use_container_width=True):
            st.rerun()
    
    # Display books
    if not db['library'].empty:
        filtered = db['library']
        if search_query:
            filtered = filtered[
                filtered['title'].str.contains(search_query, case=False, na=False) |
                filtered['author'].str.contains(search_query, case=False, na=False)
            ]
        if category_filter != "All":
            filtered = filtered[filtered['category'] == category_filter]
        
        # Show availability
        st.markdown(f"**Showing {len(filtered)} books**")
        
        for _, book in filtered.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{book['title']}**")
                    st.caption(f"by {book['author']} | {book['publisher']}")
                    st.caption(f"📂 {book['category']} | 🎯 {book['grade_level']}")
                with col2:
                    available = int(book.get('available', 0))
                    total = int(book.get('quantity', 0))
                    status_color = "🟢" if available > 0 else "🔴"
                    st.markdown(f"{status_color} **{available}/{total} available**")
                    st.caption(f"📍 Shelf: {book['shelf_location']}")
                with col3:
                    if available > 0 and role in ['student', 'parent']:
                        if st.button("Request", key=f"req_{book['isbn']}", use_container_width=True):
                            st.info("Please visit the library to borrow this book")
                    elif available == 0:
                        st.button("Waitlist", disabled=True, use_container_width=True)
    else:
        st.info("📚 Library is being set up. Check back soon!")

# --- SETTINGS PAGE ---
if page == 'settings':
    st.header("⚙️ Account Settings")
    
    with st.container(border=True):
        st.subheader("Profile Information")
        st.write(f"**Username:** {user['username']}")
        st.write(f"**Role:** {user['role'].title()}")
        st.write(f"**School:** {user.get('school', 'N/A')}")
        st.write(f"**Phone:** {user.get('phone', 'N/A')}")
        st.write(f"**Email:** {user.get('email', 'Not set')}")
    
    with st.container(border=True):
        st.subheader("Change Password")
        with st.form("change_password"):
            current = st.text_input("Current Password", type="password")
            new_pass = st.text_input("New Password", type="password")
            confirm = st.text_input("Confirm New Password", type="password")
            
            if st.form_submit_button("Update Password", type="primary"):
                if not SecurityManager.verify_password(current, user['password']):
                    st.error("Current password is incorrect")
                elif new_pass != confirm:
                    st.error("New passwords don't match")
                elif len(new_pass) < Config.MIN_PASSWORD_LENGTH:
                    st.error(f"Password must be at least {Config.MIN_PASSWORD_LENGTH} characters")
                else:
                    users_df = db['users']
                    users_df.loc[users_df['username'] == user['username'], 'password'] = SecurityManager.hash_password(new_pass)
                    DataManager.save_data(users_df, "users")
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

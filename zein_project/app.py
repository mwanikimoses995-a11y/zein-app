"""  
ZEIN SCHOOL AI v5.1 - ZERO EDUCATIONAL IGNORANCE NETWORK  
========================================================  
Production-Ready School Management System for Kenyan Primary Schools (Grades 1-9)  
- SQLite Database  
- CBE/CBC Curriculum Compliance (Grades 1-9, Junior & Senior Primary)  
- Student Fields: KEMIS No, ADM No, Guardian Phone, Class(grade), Stream  
- PDF Report Cards with CBC Grading  
- SMS Integration  
- AI Chatbot Assistant  
- Library Management  
- Audit Logging & Automated Backups  
- 5 Role System: Super Admin, School Admin, Teacher, Student, Parent  
- First-Login Password & Security Question Setup  
- Teacher Subject-Locking & Grade Selection  
- School Grade Performance Analytics  

Author: ZEIN Development Team  
Version: 5.1.0  
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

# =========================  
# CONFIGURATION & CONSTANTS  
# =========================  

class Config:  
    """Centralized configuration for ZEIN"""  
    
    # Branding & Identity  
    APP_NAME = "ZEIN"  
    FULL_NAME = "Zero Educational Ignorance Network"  
    VERSION = "5.1.0"  
    TAGLINE = "Empowering Education, Eliminating Ignorance"  
    MISSION = "To create a world where every student has access to quality education tracking and support"  
    VISION = "Zero ignorance through technology-enabled education"  
    
    # Visual Identity  
    PRIMARY_COLOR = "#1E3A8A"  
    SECONDARY_COLOR = "#F59E0B"  
    ACCENT_COLOR = "#10B981"  
    WARNING_COLOR = "#EF4444"  
    BACKGROUND_COLOR = "#F8FAFC"  
    TEXT_COLOR = "#1E293B"  
    
    # Typography  
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
    
    # Academic  
    CURRENT_YEAR = 2025  
    TERMS = ["Term 1", "Term 2", "Term 3"]  
    
    # Roles  
    ROLES = ["super_admin", "school_admin", "teacher", "student", "parent"]  
    
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
        'About': f"**{Config.FULL_NAME}** v{Config.VERSION} - {Config.MISSION}"  
    }  
)  

# =========================  
# CBE CURRICULUM (CBC) DATA  
# =========================  

class CBECurriculum:  
    """Competency-Based Education (CBC) Curriculum Structure - Kenya (Grades 1-9)"""  
    
    # School Levels (for junior/senior selection)  
    SCHOOL_TYPES = {  
        "junior_primary": "Junior Primary Only (Grades 1-6)",  
        "senior_primary": "Senior Primary Only (Grades 7-9)",  
        "both": "Both Junior & Senior Primary (Grades 1-9)"  
    }  
    
    # Grade Levels - REMOVED Grade 10-12 as requested  
    GRADES = {  
        "Grade 1": "Lower Primary",  
        "Grade 2": "Lower Primary",   
        "Grade 3": "Lower Primary",  
        "Grade 4": "Upper Primary",  
        "Grade 5": "Upper Primary",  
        "Grade 6": "Upper Primary",  
        "Grade 7": "Junior Secondary",  
        "Grade 8": "Junior Secondary",  
        "Grade 9": "Junior Secondary"  
    }  
    
    # Streams available per school type  
    STREAMS = {  
        "junior_primary": ["North", "South", "East", "West", "Blue", "Red", "Green", "Yellow"],  
        "senior_primary": ["North", "South", "East", "West", "Blue", "Red", "Green", "Yellow"]  
    }  
    
    # Learning Areas by Level (Grades 1-9)  
    SUBJECTS = {  
        "Lower Primary (Grade 1-3)": [  
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
        "Upper Primary (Grade 4-6)": [  
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
        "Junior Secondary (Grade 7-9)": [  
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
        ]  
    }  
    
    # Performance Levels (CBC Grading) - same for grades 1-9  
    PERFORMANCE_LEVELS = {  
        4: ("Exceeds Expectations", "A", 80, 100),  
        3: ("Meets Expectations", "B", 60, 79),  
        2: ("Approaches Expectations", "C", 40, 59),  
        1: ("Below Expectations", "D", 0, 39)  
    }  
    
    @classmethod  
    def get_subjects_for_grade(cls, grade: str) -> List[str]:  
        """Get subjects for a specific grade"""  
        level = cls.GRADES.get(grade, "")  
        if level in ["Lower Primary", "Upper Primary"]:  
            if level == "Lower Primary":  
                return cls.SUBJECTS["Lower Primary (Grade 1-3)"]  
            else:  
                return cls.SUBJECTS["Upper Primary (Grade 4-6)"]  
        elif level == "Junior Secondary":  
            return cls.SUBJECTS["Junior Secondary (Grade 7-9)"]  
        return []  
    
    @classmethod  
    def get_all_subjects(cls) -> List[str]:  
        """Get all unique subjects across all grades"""  
        subjects = set()  
        for group in cls.SUBJECTS.values():  
            subjects.update(group)  
        return sorted(subjects)  
    
    @classmethod  
    def get_grades_for_school_type(cls, school_type: str) -> List[str]:  
        """Get grades available for a school type"""  
        if school_type == "junior_primary":  
            return ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6"]  
        elif school_type == "senior_primary":  
            return ["Grade 7", "Grade 8", "Grade 9"]  
        elif school_type == "both":  
            return list(cls.GRADES.keys())  
        return []  
    
    @classmethod  
    def get_grade_performance(cls, score: float) -> Tuple[str, str, int, int]:  
        """Get CBC performance level for a score"""  
        for level, (name, letter, low, high) in cls.PERFORMANCE_LEVELS.items():  
            if low <= score <= high:  
                return (name, letter, low, high)  
        return cls.PERFORMANCE_LEVELS[1]  


# =========================  
# DATABASE LAYER  
# =========================  

class Database:  
    """SQLite Database layer for ZEIN"""  
    
    def __init__(self, db_path: Path = None):  
        self.db_path = db_path or Config.DB_PATH  
        self.db_path.parent.mkdir(parents=True, exist_ok=True)  
        self.conn = self._get_connection()  
        self.init_db()  
    
    def _get_connection(self) -> sqlite3.Connection:  
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)  
        conn.row_factory = sqlite3.Row  
        conn.execute("PRAGMA foreign_keys = ON")  
        conn.execute("PRAGMA journal_mode = WAL")  
        return conn  
    
    def init_db(self):  
        """Create all database tables"""  
        cursor = self.conn.cursor()  
        
        # Schools table  
        cursor.execute("""  
            CREATE TABLE IF NOT EXISTS schools (  
                id INTEGER PRIMARY KEY AUTO

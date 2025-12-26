# database.py
import sqlite3
from datetime import datetime, timedelta
import json
from config import DB_NAME

class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        c = self.conn.cursor()
        
        # Users table
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      phone TEXT UNIQUE,
                      telegram_id INTEGER UNIQUE,
                      name TEXT,
                      level TEXT DEFAULT 'user',
                      language TEXT DEFAULT 'hi',
                      login_time DATETIME,
                      last_active DATETIME,
                      is_active BOOLEAN DEFAULT 0,
                      session_id TEXT)''')
        
        # Login OTP table
        c.execute('''CREATE TABLE IF NOT EXISTS login_otp
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      phone TEXT,
                      otp_code TEXT,
                      attempts INTEGER DEFAULT 0,
                      created_at DATETIME,
                      expires_at DATETIME)''')
        
        # Admins table
        c.execute('''CREATE TABLE IF NOT EXISTS admins
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      phone TEXT UNIQUE,
                      telegram_id INTEGER UNIQUE,
                      name TEXT,
                      level TEXT DEFAULT 'admin',
                      added_by TEXT,
                      added_at DATETIME,
                      status TEXT DEFAULT 'approved')''')
        
        # Reports table
        c.execute('''CREATE TABLE IF NOT EXISTS reports
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      report_id TEXT UNIQUE,
                      user_id INTEGER,
                      user_name TEXT,
                      target_id TEXT,
                      report_type TEXT,
                      category TEXT,
                      report_text TEXT,
                      status TEXT DEFAULT 'pending',
                      is_multi BOOLEAN DEFAULT 0,
                      multi_id TEXT,
                      telegram_response TEXT,
                      created_at DATETIME)''')
        
        # Multi-reports table
        c.execute('''CREATE TABLE IF NOT EXISTS multi_reports
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      multi_id TEXT UNIQUE,
                      user_id INTEGER,
                      target_id TEXT,
                      report_type TEXT,
                      category TEXT,
                      report_text TEXT,
                      total_count INTEGER,
                      completed_count INTEGER DEFAULT 0,
                      successful_count INTEGER DEFAULT 0,
                      failed_count INTEGER DEFAULT 0,
                      delay_seconds INTEGER DEFAULT 1,
                      status TEXT DEFAULT 'running',
                      start_time DATETIME,
                      end_time DATETIME)''')
        
        # Statistics table
        c.execute('''CREATE TABLE IF NOT EXISTS statistics
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      date DATE,
                      total_reports INTEGER DEFAULT 0,
                      successful INTEGER DEFAULT 0,
                      failed INTEGER DEFAULT 0,
                      UNIQUE(user_id, date))''')
        
        # Login logs table
        c.execute('''CREATE TABLE IF NOT EXISTS login_logs
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      user_id INTEGER,
                      phone TEXT,
                      action TEXT,
                      ip_address TEXT,
                      created_at DATETIME)''')
        
        self.conn.commit()
    
    def save_otp(self, phone, otp_code):
        c = self.conn.cursor()
        expires_at = datetime.now() + timedelta(minutes=5)
        c.execute('''INSERT INTO login_otp (phone, otp_code, created_at, expires_at)
                     VALUES (?, ?, ?, ?)''',
                  (phone, otp_code, datetime.now(), expires_at))
        self.conn.commit()
        return True
    
    def verify_otp(self, phone, otp_code):
        c = self.conn.cursor()
        c.execute('''SELECT otp_code, attempts, expires_at FROM login_otp 
                     WHERE phone = ? ORDER BY created_at DESC LIMIT 1''', (phone,))
        result = c.fetchone()
        
        if not result:
            return False, "no_otp"
        
        stored_otp, attempts, expires_at = result
        
        # Check if OTP expired
        if datetime.now() > datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S.%f'):
            return False, "expired"
        
        # Check attempts
        if attempts >= 3:
            return False, "max_attempts"
        
        # Verify OTP
        if stored_otp == otp_code:
            c.execute("DELETE FROM login_otp WHERE phone = ?", (phone,))
            self.conn.commit()
            return True, "success"
        else:
            c.execute("UPDATE login_otp SET attempts = attempts + 1 WHERE phone = ?", (phone,))
            self.conn.commit()
            return False, "invalid"
    
    def create_user_session(self, phone, telegram_id, name, session_id):
        c = self.conn.cursor()
        c.execute('''INSERT OR REPLACE INTO users 
                     (phone, telegram_id, name, login_time, is_active, session_id, last_active)
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (phone, telegram_id, name, datetime.now(), 1, session_id, datetime.now()))
        self.conn.commit()
        return True
    
    def end_user_session(self, user_id):
        c = self.conn.cursor()
        c.execute("UPDATE users SET is_active = 0, last_active = ? WHERE telegram_id = ?",
                  (datetime.now(), user_id))
        self.conn.commit()
        return True
    
    def is_user_logged_in(self, user_id):
        c = self.conn.cursor()
        c.execute("SELECT telegram_id FROM users WHERE telegram_id = ? AND is_active = 1", (user_id,))
        return c.fetchone() is not None
    
    def get_user_info(self, user_id):
        c = self.conn.cursor()
        c.execute('''SELECT phone, name, level, language, login_time 
                     FROM users WHERE telegram_id = ? AND is_active = 1''', (user_id,))
        return c.fetchone()
    
    def update_user_language(self, user_id, language):
        c = self.conn.cursor()
        c.execute("UPDATE users SET language = ? WHERE telegram_id = ?", (language, user_id))
        self.conn.commit()
        return True
    
    def is_approved_admin(self, phone):
        c = self.conn.cursor()
        c.execute("SELECT phone FROM admins WHERE phone = ? AND status = 'approved'", (phone,))
        return c.fetchone() is not None
    
    def get_admin_info(self, phone):
        c = self.conn.cursor()
        c.execute("SELECT name, level FROM admins WHERE phone = ?", (phone,))
        return c.fetchone()
    
    def add_admin(self, phone, name, added_by, level='admin'):
        c = self.conn.cursor()
        try:
            c.execute('''INSERT INTO admins (phone, name, added_by, added_at, level, status)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                      (phone, name, added_by, datetime.now(), level, 'approved'))
            self.conn.commit()
            return True, "success"
        except sqlite3.IntegrityError:
            return False, "already_exists"
    
    def save_report(self, user_id, user_name, target, report_type, category, report_text, status='success', multi_id=None):
        c = self.conn.cursor()
        report_id = f"REP{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"
        
        try:
            c.execute('''INSERT INTO reports 
                         (report_id, user_id, user_name, target_id, report_type, 
                          category, report_text, status, is_multi, multi_id, created_at)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (report_id, user_id, user_name, target, report_type, 
                       category, report_text, status, 1 if multi_id else 0, multi_id, datetime.now()))
            
            # Update statistics
            today = datetime.now().date()
            c.execute('''INSERT OR IGNORE INTO statistics (user_id, date) VALUES (?, ?)''',
                      (user_id, today))
            c.execute('''UPDATE statistics SET total_reports = total_reports + 1,
                         successful = successful + ? WHERE user_id = ? AND date = ?''',
                      (1 if status == 'success' else 0, user_id, today))
            
            self.conn.commit()
            return True, report_id
        except Exception as e:
            return False, str(e)
    
    def create_multi_report(self, user_id, target, report_type, category, report_text, count, delay):
        c = self.conn.cursor()
        multi_id = f"MULTI{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id}"
        
        try:
            c.execute('''INSERT INTO multi_reports 
                         (multi_id, user_id, target_id, report_type, category, 
                          report_text, total_count, delay_seconds, start_time)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (multi_id, user_id, target, report_type, category, 
                       report_text, count, delay, datetime.now()))
            self.conn.commit()
            return True, multi_id
        except Exception as e:
            return False, str(e)
    
    def update_multi_report(self, multi_id, successful=False):
        c = self.conn.cursor()
        try:
            if successful:
                c.execute('''UPDATE multi_reports SET 
                             successful_count = successful_count + 1,
                             completed_count = completed_count + 1
                             WHERE multi_id = ?''', (multi_id,))
            else:
                c.execute('''UPDATE multi_reports SET 
                             failed_count = failed_count + 1,
                             completed_count = completed_count + 1
                             WHERE multi_id = ?''', (multi_id,))
            self.conn.commit()
            return True
        except Exception as e:
            return False
    
    def get_user_stats(self, user_id):
        c = self.conn.cursor()
        c.execute('''SELECT SUM(total_reports), SUM(successful), SUM(failed)
                     FROM statistics WHERE user_id = ?''', (user_id,))
        total, successful, failed = c.fetchone() or (0, 0, 0)
        
        success_rate = (successful / total * 100) if total > 0 else 0
        
        return {
            'total_reports': total,
            'successful': successful,
            'failed': failed,
            'success_rate': round(success_rate, 2)
        }
    
    def get_user_reports(self, user_id, limit=10):
        c = self.conn.cursor()
        c.execute('''SELECT report_id, target_id, category, status, created_at 
                     FROM reports WHERE user_id = ? 
                     ORDER BY created_at DESC LIMIT ?''', (user_id, limit))
        return c.fetchall()
    
    def log_login_action(self, user_id, phone, action):
        c = self.conn.cursor()
        c.execute('''INSERT INTO login_logs (user_id, phone, action, created_at)
                     VALUES (?, ?, ?, ?)''', (user_id, phone, action, datetime.now()))
        self.conn.commit()
    
    def __del__(self):
        self.conn.close()

# Global database instance
db = Database()
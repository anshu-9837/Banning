# login_system.py
import random
import asyncio
from datetime import datetime
from database import db
from config import MAX_LOGIN_ATTEMPTS, OTP_EXPIRE_MINUTES

class LoginSystem:
    @staticmethod
    def generate_otp():
        """Generate 6-digit OTP"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def validate_phone(phone):
        """Validate phone number format"""
        # Remove any non-digit characters
        phone = ''.join(filter(str.isdigit, phone))
        
        # Check if it's a valid Indian phone number
        if len(phone) == 10 and phone.startswith(('6', '7', '8', '9')):
            return f"+91{phone}"  # Add India country code
        elif len(phone) == 12 and phone.startswith('91'):
            return f"+{phone}"
        else:
            return None
    
    async def send_otp(self, phone):
        """Send OTP to phone (simulated for demo)"""
        clean_phone = self.validate_phone(phone)
        if not clean_phone:
            return False, "Invalid phone number"
        
        # Check if user is approved admin
        if not db.is_approved_admin(clean_phone):
            return False, "Phone number not approved"
        
        # Generate OTP
        otp_code = self.generate_otp()
        
        # Save OTP to database
        db.save_otp(clean_phone, otp_code)
        
        # In real implementation, send SMS via Twilio/MessageBird
        # For demo, we'll just return the OTP
        print(f"📱 OTP for {clean_phone}: {otp_code}")
        
        return True, f"OTP sent to {clean_phone[:8]}****"
    
    async def verify_otp_and_login(self, phone, otp_code, telegram_id, name):
        """Verify OTP and create user session"""
        clean_phone = self.validate_phone(phone)
        if not clean_phone:
            return False, "Invalid phone number"
        
        # Verify OTP
        success, message = db.verify_otp(clean_phone, otp_code)
        
        if not success:
            return False, message
        
        # Get admin info
        admin_info = db.get_admin_info(clean_phone)
        if not admin_info:
            return False, "Admin not found"
        
        name, level = admin_info
        
        # Create user session
        session_id = f"SESS{datetime.now().strftime('%Y%m%d%H%M%S')}{random.randint(1000, 9999)}"
        db.create_user_session(clean_phone, telegram_id, name, session_id)
        
        # Log login action
        db.log_login_action(telegram_id, clean_phone, "login_success")
        
        return True, {"name": name, "level": level, "phone": clean_phone}
    
    async def logout(self, telegram_id):
        """Logout user"""
        user_info = db.get_user_info(telegram_id)
        if user_info:
            phone, name, level, language, login_time = user_info
            db.end_user_session(telegram_id)
            db.log_login_action(telegram_id, phone, "logout")
            return True
        return False

# Global login system instance
login_system = LoginSystem()
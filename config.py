# config.py
import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("8323762114:AAEI3zHcuF2k59ASqbedQmQlq84WpL4HjOU")

# Approved Admins (Telegram IDs)
APPROVED_ADMINS = {
    7175613677: {"DANGER PAPA ": "", "level": "superadmin", "status": "approved"},
}

# Database Configuration
DB_NAME = "telegram_reports.db"

# Login Configuration
MAX_LOGIN_ATTEMPTS = 3
OTP_EXPIRE_MINUTES = 5
SESSION_TIMEOUT_HOURS = 24

# Report Configuration
MAX_REPORTS_PER_DAY = 50
MAX_MULTI_REPORTS = 25
MAX_DELAY_SECONDS = 10

# Telegram API (for real reporting)
TELEGRAM_API_ID = os.getenv("31008458", "")
TELEGRAM_API_HASH = os.getenv("1503e7297c1617b9d662a875727944cc", "")
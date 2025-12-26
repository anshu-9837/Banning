# main.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from datetime import datetime

from config import BOT_TOKEN
from database import db
from login_system import login_system
from report_system import report_system

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Conversation States
(
    ENTER_PHONE,
    ENTER_OTP,
    SELECT_LANGUAGE,
    SELECT_TYPE,
    SELECT_CATEGORY,
    ENTER_TARGET,
    ENTER_REPORT_TEXT,
    ENTER_REPORT_COUNT,
    ENTER_DELAY,
    CONFIRM_REPORT
) = range(10)

# ============ LOGIN HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    # Check if already logged in
    if db.is_user_logged_in(user.id):
        user_info = db.get_user_info(user.id)
        if user_info:
            phone, name, level, language, login_time = user_info
            await update.message.reply_text(
                f"✅ **You are already logged in!**\n\n"
                f"👤 Name: {name}\n"
                f"📱 Phone: {phone[:8]}****\n\n"
                f"Send /help for commands."
            )
        return
    
    # Ask for phone number
    keyboard = [
        [InlineKeyboardButton("📱 Phone Format Help", callback_data="phone_help")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_login")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 **Login to Telegram Report Bot**\n\n"
        "Please send your phone number:\n"
        "• Format: 9876543210\n"
        "• Must be 10 digits\n"
        "• Indian numbers only",
        reply_markup=reply_markup
    )
    
    return ENTER_PHONE

async def handle_phone_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle phone number input"""
    phone = update.message.text.strip()
    
    # Validate phone
    clean_phone = login_system.validate_phone(phone)
    if not clean_phone:
        await update.message.reply_text(
            "❌ **Invalid phone number!**\n\n"
            "Please send a valid 10-digit Indian phone number.\n"
            "Example: 9876543210"
        )
        return ENTER_PHONE
    
    # Send OTP
    success, message = await login_system.send_otp(phone)
    
    if success:
        context.user_data['phone'] = clean_phone
        await update.message.reply_text(
            f"✅ **OTP Sent!**\n\n"
            f"{message}\n\n"
            f"Please enter the 6-digit OTP:"
        )
        return ENTER_OTP
    else:
        await update.message.reply_text(f"❌ {message}")
        return ConversationHandler.END

async def handle_otp_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle OTP input"""
    otp = update.message.text.strip()
    phone = context.user_data.get('phone')
    user = update.effective_user
    
    if not phone:
        await update.message.reply_text("❌ Session expired. Please /start again.")
        return ConversationHandler.END
    
    # Verify OTP and login
    success, result = await login_system.verify_otp_and_login(
        phone, otp, user.id, user.full_name
    )
    
    if success:
        # Show language selection
        keyboard = [
            [InlineKeyboardButton("🇮🇳 हिंदी", callback_data="lang_hi"),
             InlineKeyboardButton("🇬🇧 English", callback_data="lang_en")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "✅ **Login Successful!**\n\n"
            "Please choose your language:",
            reply_markup=reply_markup
        )
        
        return SELECT_LANGUAGE
    else:
        error_messages = {
            "invalid": "❌ Invalid OTP. Please try again.",
            "expired": "❌ OTP expired. Please /start again.",
            "max_attempts": "❌ Maximum attempts reached. Please /start again.",
            "no_otp": "❌ No OTP found. Please /start again."
        }
        await update.message.reply_text(error_messages.get(result, "❌ Login failed."))
        return ConversationHandler.END

async def handle_language_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle language selection"""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    language = query.data.split('_')[1]  # 'hi' or 'en'
    
    # Update user language
    db.update_user_language(user.id, language)
    
    # Get user info
    user_info = db.get_user_info(user.id)
    if user_info:
        phone, name, level, lang, login_time = user_info
        
        welcome_text = report_system.get_text("welcome", language,
            name=name,
            phone=phone[:8] + "****",
            level=level,
            login_time=login_time.strftime("%d/%m/%Y %H:%M:%S") if isinstance(login_time, datetime) else login_time
        )
        
        await query.edit_message_text(welcome_text)
    
    return ConversationHandler.END

async def handle_login_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle login help"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "phone_help":
        await query.edit_message_text(
            "📱 **Phone Number Format:**\n\n"
            "• Must be 10 digits\n"
            "• Must start with 6, 7, 8, or 9\n"
            "• No country code needed\n\n"
            "**Examples:**\n"
            "✅ 9876543210\n"
            "✅ 7890123456\n"
            "❌ 1234567890\n"
            "❌ 987654321\n"
            "❌ +919876543210\n\n"
            "Please send your phone number:"
        )
    elif query.data == "cancel_login":
        await query.edit_message_text("❌ Login cancelled.")
        return ConversationHandler.END

# ============ REPORT HANDLERS ============
async def report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /report command"""
    user = update.effective_user
    
    # Check if logged in
    if not db.is_user_logged_in(user.id):
        await update.message.reply_text("❌ Please login first with /start")
        return
    
    # Get user info
    user_info = db.get_user_info(user.id)
    if not user_info:
        await update.message.reply_text("❌ User not found. Please login again.")
        return
    
    phone, name, level, language, login_time = user_info
    
    context.user_data['user_id'] = user.id
    context.user_data['user_name'] = name
    context.user_data['language'] = language
    context.user_data['is_multi'] = False
    
    # Create report type buttons
    keyboard = []
    for report_type in ["account", "channel", "group"]:
        display_name = report_system.get_report_type_name(report_type, language)
        keyboard.append([InlineKeyboardButton(display_name, callback_data=f"type_{report_type}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        report_system.get_text("choose_report_type", language),
        reply_markup=reply_markup
    )
    
    return SELECT_TYPE

async def handle_report_type(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle report type selection"""
    query = update.callback_query
    await query.answer()
    
    report_type = query.data.split('_')[1]
    context.user_data['report_type'] = report_type
    language = context.user_data.get('language', 'hi')
    
    # Create category buttons
    keyboard = []
    row = []
    
    for idx, (cat_key, cat_data) in enumerate(report_system.CATEGORIES.items(), 1):
        row.append(InlineKeyboardButton(
            f"{idx}. {cat_data[language]}",
            callback_data=f"cat_{cat_key}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    
    if row:
        keyboard.append(row)
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
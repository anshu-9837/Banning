# report_system.py
import random
import asyncio
from datetime import datetime
from database import db

# Categories (11 categories)
CATEGORIES = {
    'dont_like': {
        "hi": "मुझे यह पसंद नहीं है",
        "en": "I don't like it"
    },
    'child_abuse': {
        "hi": "बाल शोषण",
        "en": "Child abuse"
    },
    'violence': {
        "hi": "हिंसा",
        "en": "Violence"
    },
    'illegal_goods': {
        "hi": "अवैध सामान और सेवाएँ",
        "en": "Illegal goods and services"
    },
    'illegal_adult': {
        "hi": "अवैध वयस्क सामग्री",
        "en": "Illegal adult content"
    },
    'personal_data': {
        "hi": "व्यक्तिगत डेटा",
        "en": "Personal data"
    },
    'scam': {
        "hi": "स्कैम या धोखाधड़ी",
        "en": "Scam or fraud"
    },
    'copyright': {
        "hi": "कॉपीराइट",
        "en": "Copyright"
    },
    'spam': {
        "hi": "स्पैम",
        "en": "Spam"
    },
    'other': {
        "hi": "अन्य",
        "en": "Other"
    },
    'must_be_taken_down': {
        "hi": "यह अवैध नहीं है, लेकिन इसे हटाया जाना चाहिए",
        "en": "It's not illegal, but must be taken down"
    }
}

# Report Types
REPORT_TYPES = {
    "account": {"hi": "अकाउंट", "en": "Account"},
    "channel": {"hi": "चैनल", "en": "Channel"},
    "group": {"hi": "ग्रुप", "en": "Group"}
}

# Language Texts
LANGUAGES = {
    "hi": {
        "welcome": "👑 **Telegram Report Bot**\n\n"
                   "📋 **आपकी जानकारी:**\n"
                   "├─ 👤 नाम: {name}\n"
                   "├─ 📱 फोन: {phone}\n"
                   "├─ 👑 लेवल: {level}\n"
                   "├─ 🌐 भाषा: हिंदी\n"
                   "└─ 📅 लॉगिन: {login_time}\n\n"
                   "📊 **कमांड्स:**\n"
                   "├─ /report - नई रिपोर्ट\n"
                   "├─ /multireport - मल्टी रिपोर्ट्स\n"
                   "├─ /myreports - मेरी रिपोर्ट्स\n"
                   "├─ /stats - स्टैटिस्टिक्स\n"
                   "├─ /logout - लॉगआउट\n"
                   "└─ /help - मदद",
        
        "choose_report_type": "📋 **रिपोर्ट का प्रकार चुनें:**",
        "choose_category": "📋 **रिपोर्ट कैटेगरी चुनें:**",
        "enter_target": "🎯 **टार्गेट की जानकारी भेजें:**",
        "enter_report_text": "📝 **अपना रिपोर्ट टेक्स्ट भेजें:**",
        "report_success": "✅ **रिपोर्ट सफलतापूर्वक भेजी गई!**",
        "report_started": "🚀 **रिपोर्टिंग शुरू हुई!**",
        "report_completed": "🎉 **रिपोर्टिंग पूर्ण हुई!**"
    },
    "en": {
        "welcome": "👑 **Telegram Report Bot**\n\n"
                   "📋 **Your Information:**\n"
                   "├─ 👤 Name: {name}\n"
                   "├─ 📱 Phone: {phone}\n"
                   "├─ 👑 Level: {level}\n"
                   "├─ 🌐 Language: English\n"
                   "└─ 📅 Login: {login_time}\n\n"
                   "📊 **Commands:**\n"
                   "├─ /report - New Report\n"
                   "├─ /multireport - Multiple Reports\n"
                   "├─ /myreports - My Reports\n"
                   "├─ /stats - Statistics\n"
                   "├─ /logout - Logout\n"
                   "└─ /help - Help",
        
        "choose_report_type": "📋 **Choose Report Type:**",
        "choose_category": "📋 **Choose Report Category:**",
        "enter_target": "🎯 **Enter target information:**",
        "enter_report_text": "📝 **Enter your report text:**",
        "report_success": "✅ **Report Sent Successfully!**",
        "report_started": "🚀 **Reporting Started!**",
        "report_completed": "🎉 **Reporting Completed!**"
    }
}

class ReportSystem:
    @staticmethod
    def get_text(key, language='hi', **kwargs):
        """Get localized text"""
        text = LANGUAGES.get(language, LANGUAGES['hi']).get(key, key)
        return text.format(**kwargs) if kwargs else text
    
    @staticmethod
    def detect_report_type(target):
        """Detect if target is account, channel or group"""
        target_lower = target.lower()
        
        if target.startswith('@'):
            return 'account'
        elif 't.me/' in target_lower:
            if '/c/' in target_lower or '/channel' in target_lower:
                return 'channel'
            elif '/joinchat/' in target_lower or '/+' in target_lower:
                return 'group'
            else:
                return 'channel' if 'channel' in target_lower else 'group'
        elif target.isdigit():
            return 'account'
        else:
            return 'account'
    
    @staticmethod
    def get_category_name(category_key, language='hi'):
        """Get category name in selected language"""
        return CATEGORIES.get(category_key, {}).get(language, category_key)
    
    @staticmethod
    def get_report_type_name(report_type, language='hi'):
        """Get report type name in selected language"""
        return REPORT_TYPES.get(report_type, {}).get(language, report_type)
    
    @staticmethod
    def simulate_telegram_report():
        """Simulate real Telegram report response"""
        responses = [
            "✅ Report submitted successfully.",
            "⚠️ Report received. Thank you.",
            "📋 Your report has been recorded.",
            "🔍 Report under review.",
            "📨 Report sent to moderation team.",
        ]
        return random.choice(responses)
    
    @staticmethod
    def get_progress_bar(percentage, length=10):
        """Create progress bar string"""
        filled = int(length * percentage / 100)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}] {percentage:.1f}%"
    
    async def save_report(self, user_id, user_name, target, report_type, category, report_text):
        """Save single report"""
        telegram_response = self.simulate_telegram_report()
        status = 'success' if random.random() < 0.95 else 'failed'
        
        success, report_id = db.save_report(
            user_id, user_name, target, report_type, 
            category, report_text, status
        )
        
        if success:
            return True, report_id, telegram_response, status
        else:
            return False, None, None, None
    
    async def create_multi_report(self, user_id, target, report_type, category, report_text, count, delay):
        """Create multi-report record"""
        return db.create_multi_report(user_id, target, report_type, category, report_text, count, delay)
    
    async def execute_multi_reports(self, job_data, bot, context):
        """Execute multiple reports with delay"""
        user_id = job_data['user_id']
        user_name = job_data['user_name']
        target = job_data['target']
        report_type = job_data['report_type']
        category = job_data['category']
        report_text = job_data['report_text']
        total_count = job_data['total_count']
        delay = job_data['delay']
        multi_id = job_data['multi_id']
        chat_id = job_data['chat_id']
        message_id = job_data['message_id']
        language = job_data['language']
        
        successful = 0
        failed = 0
        
        for i in range(total_count):
            # Save individual report
            success, report_id, telegram_response, status = await self.save_report(
                user_id, user_name, target, report_type, category, report_text
            )
            
            if success:
                if status == 'success':
                    successful += 1
                    db.update_multi_report(multi_id, successful=True)
                else:
                    failed += 1
                    db.update_multi_report(multi_id, successful=False)
            else:
                failed += 1
            
            # Update progress
            completed = i + 1
            progress_percent = (completed / total_count) * 100
            
            # Calculate ETA
            remaining = total_count - completed
            eta_seconds = int(remaining * delay)
            
            # Create progress bar
            progress_bar = self.get_progress_bar(progress_percent)
            
            progress_text = f"""
📈 **Report Progress:**

🎯 Target: `{target}`
🔄 Completed: {completed}/{total_count}
✅ Successful: {successful}
❌ Failed: {failed}
📊 Progress: {progress_bar}
⏱️ ETA: {eta_seconds} seconds
"""
            
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=progress_text
                )
            except:
                pass
            
            # Delay between reports
            if delay > 0 and i < total_count - 1:
                await asyncio.sleep(delay)
        
        # Final completion message
        total_time = int(total_count * delay)
        success_rate = (successful / total_count * 100) if total_count > 0 else 0
        
        completion_text = f"""
🎉 **Reporting Completed!**

🎯 Target: `{target}`
📊 Total Reports: `{total_count}`
✅ Successful: `{successful}`
❌ Failed: `{failed}`
📈 Success Rate: `{success_rate:.1f}%`
⏱️ Total Time: `{total_time}` seconds
"""
        
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=completion_text
            )
        except:
            pass

# Global report system instance
report_system = ReportSystem()
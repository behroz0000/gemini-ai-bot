import os
import telebot
import google.generativeai as genai
from PIL import Image
import time

# YANGI TOKENNI SHUYERGA QO'YING
BOT_TOKEN = 'BU_YERGA_YANGI_TOKENNI_QO_YING'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'

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

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Salom! Bot qayta tiklandi va noldan ishga tushdi. Rasm yuboring! 😎")

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
        prompt = "Ushbu rasmga qarab, o'zbek tilida qisqa, prikol, hazilomuz ta'rif yozib ber."
        
        response = model.generate_content([prompt, img])
        ai_reply = response.text

        bot.delete_message(chat_id, status_msg.message_id)
        bot.reply_to(message, f"📸 **Gemini AI:**\n\n{ai_reply}")

        if os.path.exists(local_path):
            os.remove(local_path)

    except Exception as e:
        try:
            bot.edit_message_text(f"Xatolik: {str(e)}", chat_id, status_msg.message_id)
        except:
            pass

if __name__ == "__main__":
    print("Bot ishga tushmoqda...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)

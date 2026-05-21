import os
import logging
import threading
import requests
import google.generativeai as genai
import telebot
from flask import Flask

os.environ["GOOGLE_API_VERSION"] = "v1"

BOT_TOKEN = '8822374451:AAH44tO2fOxgLgxNLw_pIazWFh1u0NTb82c'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!", 200

@app.route('/health')
def health():
    return "OK", 200

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def download_photo(file_info, save_path):
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    response = requests.get(file_url, timeout=30)
    response.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(response.content)

def analyze_image_with_gemini(image_path):
    with open(image_path, 'rb') as f:
        image_data = f.read()

    image_part = {
        "mime_type": "image/jpeg",
        "data": image_data
    }

    prompt = (
        "Siz o'zbek tilida ijodiy va kulgili sharhlar yozuvchi AI assistantsiz. "
        "Ushbu rasmga qarab, o'zbek tilida qisqa, qiziqarli va hazilomuz bir sharh yozing. "
        "Sharh 2-4 jumladan iborat bo'lsin, jonli va o'qimishli bo'lsin. "
        "Faqat sharhni yozing, boshqa narsa yozmang."
    )

    response = model.generate_content([prompt, image_part])
    return response.text.strip()

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    text = (
        "👋 Salom! Men rasm tahlil qiluvchi botman.\n\n"
        "📸 Menga istalgan rasm yuboring — men unga o'zbek tilida "
        "qiziqarli va kulgili sharh yozib beraman! 😄"
    )
    bot.reply_to(message, text)

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    chat_id = message.chat.id
    img_path = None

    try:
        bot.send_chat_action(chat_id, 'typing')
        bot.reply_to(message, "🔍 Rasm tahlil qilinmoqda, bir oz kuting...")

        photo = message.photo[-1]
        file_info = bot.get_file(photo.file_id)

        img_path = os.path.join(DOWNLOAD_DIR, f"{photo.file_id}.jpg")
        download_photo(file_info, img_path)
        logger.info(f"Rasm yuklandi: {img_path}")

        comment = analyze_image_with_gemini(img_path)
        logger.info(f"Gemini javobi: {comment}")

        bot.reply_to(message, f"🤖 {comment}")

    except requests.exceptions.RequestException as e:
        logger.error(f"Rasm yuklashda xato: {e}")
        bot.reply_to(message, "❌ Rasmni yuklab bo'lmadi. Iltimos, qayta urinib ko'ring.")

    except Exception as e:
        logger.error(f"Xato turi: {type(e).__name__}, xabar: {str(e)}")
        bot.reply_to(message, f"⚠️ Xato: {type(e).__name__}: {str(e)[:300]}")

    finally:
        if img_path and os.path.exists(img_path):
            os.remove(img_path)
            logger.info(f"Rasm o'chirildi: {img_path}")

@bot.message_handler(func=lambda message: True)
def handle_other(message):
    bot.reply_to(message, "📸 Iltimos, menga rasm yuboring. Faqat rasmlarga sharh yoza olaman!")

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Flask server {port}-portda ishga tushirilmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server thread ishga tushdi.")

    logger.info("Webhook o'chirilmoqda...")
    bot.remove_webhook()

    logger.info("Bot polling rejimida ishga tushirilmoqda...")
    bot.infinity_polling(
        timeout=10,
        long_polling_timeout=5,
        logger_level=logging.INFO,
        restart_on_change=False
    )

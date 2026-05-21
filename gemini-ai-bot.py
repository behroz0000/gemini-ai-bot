import os
import logging
import threading
import requests
import base64
import telebot
from flask import Flask

# ===================== SOZLAMALAR =====================
BOT_TOKEN = '8822374451:AAH44tO2fOxgLgxNLw_pIazWFh1u0NTb82c'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== TELEGRAM BOT =====================
bot = telebot.TeleBot(BOT_TOKEN, parse_mode=None)

# ===================== FLASK SERVER =====================
app = Flask(__name__)

@app.route('/')
def home():
    return "Bot ishlayapti!", 200

@app.route('/health')
def health():
    return "OK", 200

# ===================== DOWNLOADS PAPKASI =====================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===================== YORDAMCHI FUNKSIYALAR =====================
def download_photo(file_info, save_path):
    file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_info.file_path}"
    response = requests.get(file_url, timeout=30)
    response.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(response.content)

def analyze_image_with_gemini(image_path):
    # Rasmni base64 ga o'girish
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": (
                            "Siz o'zbek tilida ijodiy va kulgili sharhlar yozuvchi AI assistantsiz. "
                            "Ushbu rasmga qarab, o'zbek tilida qisqa, qiziqarli va hazilomuz bir sharh yozing. "
                            "Sharh 2-4 jumladan iborat bo'lsin, jonli va o'qimishli bo'lsin. "
                            "Faqat sharhni yozing, boshqa narsa yozmang."
                        )
                    },
                    {
                        "inline_data": {
                            "mime_type": "image/jpeg",
                            "data": image_data
                        }
                    }
                ]
            }
        ]
    }

    response = requests.post(GEMINI_URL, json=payload, timeout=30)
    response.raise_for_status()
    result = response.json()
    return result['candidates'][0]['content']['parts'][0]['text'].strip()

# ===================== BOT HANDLERLAR =====================
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
        logger.error(f"So'rov xatosi: {e}")
        bot.reply_to(message, "❌ Xatolik yuz berdi. Iltimos, qayta urinib ko'ring.")

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

# ===================== FLASK SERVERNI ISHGA TUSHIRISH =====================
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Flask server {port}-portda ishga tushirilmoqda...")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ===================== ASOSIY FUNKSIYA =====================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask server thread ishga tushdi.")

    import time
    logger.info("Webhook o'chirilmoqda...")
    bot.remove_webhook()
    time.sleep(2)

    logger.info("Bot polling rejimida ishga tushirilmoqda...")
    bot.infinity_polling(
        timeout=10,
        long_polling_timeout=5,
        logger_level=logging.INFO,
        restart_on_change=False,
        drop_pending_updates=True
    )

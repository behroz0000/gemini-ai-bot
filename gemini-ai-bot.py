import os
import logging
import threading
import requests
import base64
import time
from flask import Flask

# ===================== SOZLAMALAR =====================
BOT_TOKEN = '8822374451:AAH44tO2fOxgLgxNLw_pIazWFh1u0NTb82c'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
TG = f"https://api.telegram.org/bot{BOT_TOKEN}"

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

# ===================== TELEGRAM FUNKSIYALARI =====================
def tg_send(chat_id, text):
    try:
        requests.post(f"{TG}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        logger.error(f"sendMessage xato: {e}")

def tg_action(chat_id, action="typing"):
    try:
        requests.post(f"{TG}/sendChatAction", json={"chat_id": chat_id, "action": action}, timeout=5)
    except:
        pass

def tg_get_file(file_id):
    resp = requests.get(f"{TG}/getFile", params={"file_id": file_id}, timeout=10)
    return resp.json()["result"]["file_path"]

def tg_download(file_path, save_path):
    url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    with open(save_path, 'wb') as f:
        f.write(resp.content)

# ===================== GEMINI =====================
def analyze_image(image_path):
    with open(image_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode('utf-8')

    payload = {
        "contents": [{
            "parts": [
                {"text": (
                    "Siz o'zbek tilida ijodiy va kulgili sharhlar yozuvchi AI assistantsiz. "
                    "Ushbu rasmga qarab, o'zbek tilida qisqa, qiziqarli va hazilomuz bir sharh yozing. "
                    "Sharh 2-4 jumladan iborat bo'lsin, jonli va o'qimishli bo'lsin. "
                    "Faqat sharhni yozing, boshqa narsa yozmang."
                )},
                {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
            ]
        }]
    }

    resp = requests.post(GEMINI_URL, json=payload, timeout=40)
    resp.raise_for_status()
    return resp.json()['candidates'][0]['content']['parts'][0]['text'].strip()

# ===================== UPDATE QAYTA ISHLASH =====================
def handle_update(update):
    message = update.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    text = message.get("text", "")
    photos = message.get("photo", [])

    if text in ["/start", "/help"]:
        tg_send(chat_id,
            "👋 Salom! Men rasm tahlil qiluvchi botman.\n\n"
            "📸 Menga istalgan rasm yuboring — men unga o'zbek tilida "
            "qiziqarli va kulgili sharh yozib beraman! 😄"
        )
        return

    if photos:
        img_path = None
        try:
            tg_action(chat_id)
            tg_send(chat_id, "🔍 Rasm tahlil qilinmoqda, bir oz kuting...")

            photo = photos[-1]
            file_path = tg_get_file(photo["file_id"])
            img_path = os.path.join(DOWNLOAD_DIR, f"{photo['file_id']}.jpg")
            tg_download(file_path, img_path)

            comment = analyze_image(img_path)
            tg_send(chat_id, f"🤖 {comment}")

        except Exception as e:
            logger.error(f"Xato: {type(e).__name__}: {e}")
            tg_send(chat_id, f"⚠️ Xato: {type(e).__name__}: {str(e)[:200]}")
        finally:
            if img_path and os.path.exists(img_path):
                os.remove(img_path)
        return

    tg_send(chat_id, "📸 Iltimos, menga rasm yuboring. Faqat rasmlarga sharh yoza olaman!")

# ===================== POLLING =====================
def polling_loop():
    offset = None

    # Boshlashda eski sessiyalarni tozalash
    try:
        requests.post(f"{TG}/deleteWebhook", json={"drop_pending_updates": True}, timeout=10)
        logger.info("Webhook o'chirildi, eski updatelar tozalandi.")
        time.sleep(3)
    except Exception as e:
        logger.warning(f"deleteWebhook xato: {e}")

    logger.info("Polling boshlandi...")

    while True:
        try:
            params = {"timeout": 30, "limit": 100}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(f"{TG}/getUpdates", params=params, timeout=40)

            if resp.status_code == 409:
                logger.warning("409 Conflict — 10 soniya kutib qayta uriniladi...")
                time.sleep(10)
                # Yana tozalash
                requests.post(f"{TG}/deleteWebhook", json={"drop_pending_updates": True}, timeout=10)
                time.sleep(5)
                continue

            if not resp.ok:
                logger.warning(f"getUpdates xato: {resp.status_code} — 5 soniya kutilmoqda")
                time.sleep(5)
                continue

            updates = resp.json().get("result", [])

            for update in updates:
                try:
                    handle_update(update)
                except Exception as e:
                    logger.error(f"Update qayta ishlashda xato: {e}")
                offset = update["update_id"] + 1

        except requests.exceptions.Timeout:
            logger.info("Timeout — davom etilmoqda")
            continue
        except Exception as e:
            logger.error(f"Polling xato: {e} — 5 soniya kutilmoqda")
            time.sleep(5)

# ===================== FLASK =====================
def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Flask {port}-portda ishga tushdi")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

# ===================== MAIN =====================
if __name__ == '__main__':
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    polling_loop()

import os
import logging
import requests
import base64
from flask import Flask, request, jsonify

# ===================== SOZLAMALAR =====================
BOT_TOKEN = '8822374451:AAH44tO2fOxgLgxNLw_pIazWFh1u0NTb82c'
GEMINI_API_KEY = 'AIzaSyAt10c_-oKeN-1gIeTk9frpA9xuUFesPhI'
GEMINI_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite-preview-06-17:generateContent?key={GEMINI_API_KEY}"
TG = f"https://api.telegram.org/bot{BOT_TOKEN}"
WEBHOOK_URL = f"https://gemini-ai-bot-v4mb.onrender.com/{BOT_TOKEN}"

# ===================== LOGGING =====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== FLASK =====================
app = Flask(__name__)

# ===================== DOWNLOADS PAPKASI =====================
DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# ===================== TELEGRAM FUNKSIYALARI =====================
def tg_send(chat_id, text):
    try:
        requests.post(f"{TG}/sendMessage", json={"chat_id": chat_id, "text": text}, timeout=10)
    except Exception as e:
        logger.error(f"sendMessage xato: {e}")

def tg_action(chat_id):
    try:
        requests.post(f"{TG}/sendChatAction", json={"chat_id": chat_id, "action": "typing"}, timeout=5)
    except:
        pass

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

# ===================== WEBHOOK ENDPOINT =====================
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        if not update:
            return jsonify({"ok": True})

        message = update.get("message", {})
        chat_id = message.get("chat", {}).get("id")
        if not chat_id:
            return jsonify({"ok": True})

        text = message.get("text", "")
        photos = message.get("photo", [])

        if text in ["/start", "/help"]:
            tg_send(chat_id,
                "👋 Salom! Men rasm tahlil qiluvchi botman.\n\n"
                "📸 Menga istalgan rasm yuboring — men unga o'zbek tilida "
                "qiziqarli va kulgili sharh yozib beraman! 😄"
            )
            return jsonify({"ok": True})

        if photos:
            img_path = None
            try:
                tg_action(chat_id)
                tg_send(chat_id, "🔍 Rasm tahlil qilinmoqda, bir oz kuting...")

                photo = photos[-1]
                file_resp = requests.get(f"{TG}/getFile", params={"file_id": photo["file_id"]}, timeout=10)
                file_path = file_resp.json()["result"]["file_path"]

                file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
                img_resp = requests.get(file_url, timeout=30)
                img_resp.raise_for_status()

                img_path = os.path.join(DOWNLOAD_DIR, f"{photo['file_id']}.jpg")
                with open(img_path, 'wb') as f:
                    f.write(img_resp.content)

                comment = analyze_image(img_path)
                tg_send(chat_id, f"🤖 {comment}")

            except Exception as e:
                logger.error(f"Xato: {type(e).__name__}: {e}")
                tg_send(chat_id, f"⚠️ Xato: {type(e).__name__}: {str(e)[:200]}")
            finally:
                if img_path and os.path.exists(img_path):
                    os.remove(img_path)

            return jsonify({"ok": True})

        tg_send(chat_id, "📸 Iltimos, menga rasm yuboring. Faqat rasmlarga sharh yoza olaman!")

    except Exception as e:
        logger.error(f"Webhook xato: {e}")

    return jsonify({"ok": True})

# ===================== HEALTH CHECK =====================
@app.route('/')
def home():
    return "Bot ishlayapti!", 200

@app.route('/health')
def health():
    return "OK", 200

@app.route('/set_webhook')
def set_webhook():
    resp = requests.post(f"{TG}/setWebhook", json={"url": WEBHOOK_URL})
    return jsonify(resp.json())

@app.route('/webhook_info')
def webhook_info():
    resp = requests.get(f"{TG}/getWebhookInfo")
    return jsonify(resp.json())

# ===================== MAIN =====================
if __name__ == '__main__':
    try:
        resp = requests.post(f"{TG}/setWebhook", json={"url": WEBHOOK_URL}, timeout=10)
        logger.info(f"Webhook o'rnatildi: {resp.json()}")
    except Exception as e:
        logger.error(f"Webhook o'rnatishda xato: {e}")

    port = int(os.environ.get('PORT', 10000))
    logger.info(f"Flask {port}-portda ishga tushdi")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)

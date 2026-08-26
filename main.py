import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
import yt_dlp

# Render muhit o'zgaruvchilaridan tokenlarni o'qish
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)
user_modes = {}

# Render port talabini qondirish uchun kichik veb-server
class SimpleHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running successfully!")

def run_web_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_modes[user_id] = None
    
    keyboard = [
        [KeyboardButton("🤖 AI bilan suhbat"), KeyboardButton("🎵 Musiqa topuvchi")],
        [KeyboardButton("💡 Bot haqida"), KeyboardButton("❓ Yordam"), KeyboardButton("🔄 Start")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Salom! Kerakli bo'limni tanlang:", reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_text = update.message.text.strip()

    if user_text in ["🔄 Start", "/start"]:
        await start(update, context)
        return
    elif user_text == "💡 Bot haqida":
        await update.message.reply_text("Ushbu bot Zoxid tomonidan yaratilgan AI va YouTube Music bazasida ishlaydi.")
        return
    elif user_text == "❓ Yordam":
        await update.message.reply_text("Musiqa yuklash uchun '🎵 Musiqa topuvchi' tugmasini bosing va qo'shiq nomini yozing.")
        return
    elif user_text == "🤖 AI bilan suhbat":
        user_modes[user_id] = "ai"
        await update.message.reply_text("🤖 AI rejimi yoqildi! Savolingizni yuboring:")
        return
    elif user_text == "🎵 Musiqa topuvchi":
        user_modes[user_id] = "music"
        await update.message.reply_text("🎵 Musiqa rejimi yoqildi! Qo'shiq nomini yozing:")
        return

    current_mode = user_modes.get(user_id)
    if not current_mode:
        await update.message.reply_text("Iltimos, pastdagi tugmalardan birini bosing!")
        return

    if current_mode == "music":
        msg = await update.message.reply_text("🎵 Qo'shiq qidirilmoqda va yuklanmoqda...")
        ydl_opts = {
            'format': 'bestaudio/best', 
            'outtmpl': 'song.%(ext)s', 
            'default_search': 'ytsearch1', 
            'noplaylist': True, 
            'quiet': True,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
        }
        
        filename = None
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(user_text, download=True)
                filename = ydl.prepare_filename(info['entries'][0]) if 'entries' in info else ydl.prepare_filename(info)
                title = info['entries'][0].get('title', 'Musiqa') if 'entries' in info else info.get('title', 'Musiqa')
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=title)
            
            await msg.delete()
        except Exception as e:
            await msg.edit_text(f"Xatolik: {e}")
        finally:
            if filename and os.path.exists(filename):
                os.remove(filename)

    elif current_mode == "ai":
        try:
            # Model nomi gemini-2.0-flash ga to'g'irlandi
            response = client.models.generate_content(model="gemini-2.0-flash", contents=user_text)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")

if __name__ == '__main__':
    server_thread = threading.Thread(target=run_web_server, daemon=True)
    server_thread.start()

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
    

import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai
import yt_dlp

TELEGRAM_BOT_TOKEN = "8766446426:AAEajDOdYmmDDnV5t_kY07Ljog4SoeKSm0M"
GEMINI_API_KEY = "AQ.Ab8RN6Jq7yDxeG-wk99AT4rHnkaQUHmK7wD3E1-q3pkdac8lxQ"

client = genai.Client(api_key=GEMINI_API_KEY)
user_modes = {}

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
        await update.message.reply_text("Ushbu bot Gemini AI va YouTube Music bazasida ishlaydi.")
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
        ydl_opts = {'format': 'bestaudio/best', 'outtmpl': 'song.%(ext)s', 'default_search': 'ytsearch1', 'noplaylist': True, 'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(user_text, download=True)
                filename = ydl.prepare_filename(info['entries'][0]) if 'entries' in info else ydl.prepare_filename(info)
                title = info['entries'][0].get('title', 'Musiqa') if 'entries' in info else info.get('title', 'Musiqa')
            
            with open(filename, 'rb') as audio_file:
                await update.message.reply_audio(audio=audio_file, title=title)
            
            await msg.delete()
            if os.path.exists(filename): os.remove(filename)
        except Exception as e:
            await msg.edit_text(f"Xatolik: {e}")

    elif current_mode == "ai":
        try:
            response = client.models.generate_content(model="gemini-2.5-flash", contents=user_text)
            await update.message.reply_text(response.text)
        except Exception as e:
            await update.message.reply_text(f"Xatolik: {e}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()
  

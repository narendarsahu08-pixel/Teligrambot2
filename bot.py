import os
import requests
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'Hello! I am your AI bot. Ask me anything.\n'
        'Use /image <description> to generate an image.'
    )

async def send_long_message(update: Update, text: str) -> None:
    """Telegram has a 4096 character limit per message. Split long replies into chunks."""
    max_len = 4000
    for i in range(0, len(text), max_len):
        await update.message.reply_text(text[i:i + max_len])

async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_message = update.message.text
    try:
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": user_message}]
            },
            timeout=60
        )
        data = response.json()
        print(data)
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
        else:
            reply = f"Error: {data}"
    except Exception as e:
        reply = f"Something went wrong: {e}"

    await send_long_message(update, reply)

async def generate_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("Please provide a description. Example: /image a cat riding a bicycle")
        return

    await update.message.reply_text("Generating image, please wait...")
    try:
        encoded_prompt = requests.utils.quote(prompt)
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        img_response = requests.get(image_url, timeout=60)
        if img_response.status_code == 200:
            await update.message.reply_photo(photo=img_response.content, caption=prompt)
        else:
            await update.message.reply_text("Sorry, image generation failed. Try again.")
    except Exception as e:
        await update.message.reply_text(f"Image generation error: {e}")

def main() -> None:
    threading.Thread(target=run_flask).start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("image", generate_image))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat))
    application.run_polling()

if __name__ == "__main__":
    main()

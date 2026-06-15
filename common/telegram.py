from settings import *
import os
from telegram import Bot
from telegram.ext import ApplicationBuilder
from dotenv import load_dotenv

load_dotenv()

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
application = ApplicationBuilder().token(bot_token).build()
default_chat_id = os.environ.get("TELEGRAM_CHAT_ID")


async def check_permissions(username, update, context):
    if username in valid_users:
        return True
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text="Neturite tokių teisių.",
        )
        return False


async def send_mqtt_state_to_telegram(text, chatid):
    async with Bot(bot_token) as bot:
        await bot.send_message(chat_id=chatid, text=text)

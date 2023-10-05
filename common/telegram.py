from settings import *
import os
from telegram.ext import ApplicationBuilder

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
application = ApplicationBuilder().token(bot_token).build()
default_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

def check_permissions(username, update, context):
    if username in valid_users:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Neturite tokių teisių.",
        )
        return False

async def send_mqtt_state_to_telegram(text, chatid):
    app = ApplicationBuilder().token(bot_token).build()
    await app.bot.send_message(chat_id=chatid, text=text)

    # alternative method, maybe simpler
    # await telegram.Bot(bot_token).send_message(
    #     chat_id=chatid,
    #     text=text,
    # )

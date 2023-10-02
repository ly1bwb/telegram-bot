from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
import logging

from settings import *

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)
    return ConversationHandler.END

log = logging
log.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def log_func(name, update):
    log.info(f"Called {name} by {update.message.from_user['username']}")


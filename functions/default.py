import logging
import socket
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from common.telegram import *
from settings import *

CAM, VHF_FREQ, VHF_AZ, VHF_EL, HF_AZ, VHF_MODE, VHF_SDR_STAT, UHF_SDR_STAT, MONITORS, LIGHTS = range(10)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)
    return ConversationHandler.END

log = logging
log.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def log_func(name, update):
    log.info(f"Called {name} by {update.message.from_user['username']}")

def format_frequency(f):
    return f[-9] + f[-8] + f[-7] + "." + f[-6] + f[-5] + f[-4] + " MHz"

async def sveiki(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("sveiki()", update)
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sveiki")
    return ConversationHandler.END

async def get_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("get_status()", update)
    username = update.message.from_user["username"]
    if check_permissions(username, update, context):
        hostname = socket.gethostname()
        ip_address = socket.gethostbyname(hostname)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Version: {VERSION}\nHostname: {hostname}\nIP: {ip_address}"
        )
    return ConversationHandler.END

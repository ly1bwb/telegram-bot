from functions.default import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode
from qrz import QRZ

def print_keys(key_names, query_result):
    info = ""
    for key_name in key_names:
        if key_name in query_result:
            info += query_result[key_name] + " "
    print(info)
    return info

async def whois_qrz_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("whois_qrz_query()", update)
    username = update.message.from_user["username"]

    if check_permissions(username, update, context):
        if len(context.args) == 1:
            callsign = context.args[0].upper()

            await context.bot.send_chat_action(
                chat_id=update.effective_chat.id, message_thread_id=update.effective_message.message_thread_id, action=ChatAction.TYPING
            )

            try:
                qrz = QRZ()
                result = qrz.callsign(callsign)
                answ1 = print_keys(['fname', 'name'], result)
                answ2 = print_keys(['addr2', 'state'], result)
                answ3 = print_keys(['country'], result)
                full_answ = f"{callsign}\n{answ1}\n{answ2}\n{answ3}"
            except Exception as e:
                print(f"Error: {e}")
                full_answ = f"{callsign} - {e}"

            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.effective_message.message_thread_id,
                text=full_answ,
            )

        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.effective_message.message_thread_id,
                text=f"whois <callsign>",
            )
    return ConversationHandler.END

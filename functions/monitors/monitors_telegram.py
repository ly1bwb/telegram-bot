from functions.default import *
from functions.monitors.monitors_mqtt import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode

async def set_monitors_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(
        f"Called set_monitors_state() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        new_state = context.args[-1].upper()

        if new_state == "ON" or new_state == "OFF":
            if new_state != get_monitors_state():
                msg_action = "Įjungiu" if new_state == "ON" else "Išjungiu"
                msg = (
                    f"{msg_action} monitorius"
                )
                change_monitors_state(new_state)
            else:
                if get_monitors_state() == "ON":
                    msg_action = "Įjungti"
                elif get_monitors_state() == "OFF":
                    msg_action = "Išjungti"
                else:
                    msg_action = "Nežinoma būsena"
                msg = (
                    f"Monitoriai jau yra {msg_action}"
                )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Neteisingas parametras"
            )
    else:
        options = [
            [
                InlineKeyboardButton(text="ON", callback_data="on"),
                InlineKeyboardButton(text="OFF", callback_data="off"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)

        if get_monitors_state() == "ON":
            msg_action = "Įjungti"
        elif get_monitors_state() == "OFF":
            msg_action = "Išjungti"
        else:
            msg_action = "Nežinoma būsena"

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Dabar monitoriai yra <b>{msg_action}</b>\nPasirinkite arba įveskite naują monitorių būseną:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    return MONITORS

async def read_monitors_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_monitors_state()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]

    if check_permissions(username, update, context):
        new_state = query.data.upper()
        old_state = get_monitors_state()

        if new_state == "ON" or new_state == "OFF":
            if new_state != old_state:
                msg_state = "Įjungiu" if new_state == "ON" else "Išjungiu"
                msg = (
                    f"{msg_state} monitorius"
                )
                change_monitors_state(new_state)
            else:
                if get_monitors_state() == "ON":
                    msg_action = "Įjungti"
                elif get_monitors_state() == "OFF":
                    msg_action = "Išjungti"
                else:
                    msg_action = "Nežinoma būsena"
                msg = (
                    f"Monitoriai jau yra {msg_action}"
                )
            await query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, text=f"Neteisingas parametras"
            )
    return ConversationHandler.END

monitors_state_handler = ConversationHandler(
    entry_points=[CommandHandler("monitors", set_monitors_state)],
    states={MONITORS: [CallbackQueryHandler(read_monitors_state)]},
    fallbacks=[CommandHandler("monitors", set_monitors_state)],
)

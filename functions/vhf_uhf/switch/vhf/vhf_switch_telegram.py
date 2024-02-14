from functions.default import *
from functions.vhf_uhf.switch.vhf.vhf_switch_mqtt import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode

async def set_vhf_sdr_switch_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(
        f"Called set_vhf_sdr_switch_state() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        new_state = context.args[-1].upper()

        if new_state == "ON" or new_state == "OFF":
            if new_state != get_vhf_sdr_state():
                msg = (
                    "Perjungiu VHF MFJ Switch state iš <b>"
                    + get_vhf_sdr_state()
                    + "</b> į <b>"
                    + new_state
                    + "</b>"
                )
                change_vhf_sdr_state(new_state)
            else:
                msg = (
                    "VHF MFJ Switch jau yra <b>"
                    + new_state
                    + "</b>"
                )
            await context.bot.send_message(
                chat_id=update.effective_chat.id, message_thread_id=update.effective_message.message_thread_id, text=msg, parse_mode=ParseMode.HTML
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, message_thread_id=update.effective_message.message_thread_id, text=f"Neteisingas parametras"
            )
    else:
        options = [
            [
                InlineKeyboardButton(text="ON", callback_data="on"),
                InlineKeyboardButton(text="OFF", callback_data="off"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Dabar MFJ VHF Switch yra <b>{get_vhf_sdr_state()}</b>\nPasirinkite arba įveskite naują MFJ Switch būseną:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    return VHF_SDR_STAT

async def read_vhf_sdr_switch_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_sdr_switch_state()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]

    if check_permissions(username, update, context):
        new_state = query.data.upper()
        old_state = get_vhf_sdr_state()

        if new_state == "ON" or new_state == "OFF":
            if new_state != old_state:
                msg = (
                    "Perjungiu MFJ VHF Switch state iš <b>"
                    + get_vhf_sdr_state()
                    + "</b> į <b>"
                    + new_state
                    + "</b>"
                )
                change_vhf_sdr_state(new_state)
            else:
                msg = (
                    "MFJ VHF Switch jau yra <b>"
                    + new_state
                    + "</b>"
                )
            await query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id, message_thread_id=update.effective_message.message_thread_id, text=f"Neteisingas parametras"
            )
    return ConversationHandler.END

vhf_sdr_state_handler = ConversationHandler(
    entry_points=[CommandHandler("vhf_sdr", set_vhf_sdr_switch_state)],
    states={VHF_SDR_STAT: [CallbackQueryHandler(read_vhf_sdr_switch_state)]},
    fallbacks=[CommandHandler("vhf_sdr", set_vhf_sdr_switch_state)],
)

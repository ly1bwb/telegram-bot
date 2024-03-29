from functions.default import *
from functions.vhf_uhf.radio.vhf_uhf_radio_mqtt import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode


async def vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ff = format_frequency(get_vhf_rig_freq())
    src_mode = get_vhf_rig_mode()
    if src_mode == "FM":
        mm = "nfm"
    elif src_mode == "AM":
        mm = "am"
    elif src_mode == "USB":
        mm = "usb"
    elif src_mode == "LSB":
        mm = "lsb"
    elif src_mode == "CW" or src_mode == "CWR":
        mm = "cw"
    else:
        mm = "nfm"

    msg = (
        "VHF stoties dažnis: \n<b>"
        + ff
        + " ("
        + get_vhf_rig_mode()
        + ")</b>"
        + "\n👉 <a href='http://sdr.vhf.lt:8073/#freq="
        + get_vhf_rig_freq()
        + ",mod="
        + mm
        + "'>Klausyti gyvai</a>"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        text=msg,
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def read_vhf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_mode()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    f1 = get_vhf_rig_mode()
    f2 = query.data
    if check_permissions(username, update, context):
        change_vhf_mode(query.data)
        await query.edit_message_text(text=f"Keičiu režimą iš {f1} į {f2}")
    return ConversationHandler.END


async def set_vhf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Called set_vhf_mode() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_vhf_mode(context.args[-1])
        f1 = get_vhf_rig_mode()
        f2 = context.args[-1]
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Keičiu režimą iš {f1} į {f2}",
        )
    else:
        options = [
            [
                InlineKeyboardButton(text="FM", callback_data="FM"),
                InlineKeyboardButton(text="USB", callback_data="USB"),
                InlineKeyboardButton(text="LSB", callback_data="LSB"),
            ],
            [
                InlineKeyboardButton(text="CW", callback_data="CW"),
                InlineKeyboardButton(text="CWR", callback_data="CWR"),
                InlineKeyboardButton(text="AM", callback_data="AM"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Pasirinkite režimą (dabar {get_vhf_rig_mode()}):",
            reply_markup=reply_markup,
        )
        return VHF_MODE


async def read_vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_freq()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    f1 = format_frequency(get_vhf_rig_freq())
    f2 = format_frequency(query.data)
    if check_permissions(username, update, context):
        change_vhf_freq(query.data)
        await query.edit_message_text(text=f"Keičiu dažnį iš {f1} į {f2}")
    return ConversationHandler.END


async def set_vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Called set_vhf_freq() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_vhf_freq(context.args[-1])
        f1 = format_frequency(get_vhf_rig_freq())
        f2 = format_frequency(context.args[-1])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Keičiu dažnį iš {f1} į {f2}",
        )
    else:
        options = [
            [
                InlineKeyboardButton(text="144.050", callback_data="144050000"),
                InlineKeyboardButton(text="144.300", callback_data="144300000"),
                InlineKeyboardButton(text="144.800", callback_data="144800000"),
            ],
            [
                InlineKeyboardButton(text="145.500", callback_data="145500000"),
                InlineKeyboardButton(text="145.800", callback_data="145800000"),
                InlineKeyboardButton(text="145.825", callback_data="145825000"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text="Pasirinkite arba įveskite dažnį:",
            reply_markup=reply_markup,
        )
        return VHF_FREQ


vhf_freq_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_freq", set_vhf_freq)],
    states={VHF_FREQ: [CallbackQueryHandler(read_vhf_freq)]},
    fallbacks=[CommandHandler("set_vhf_freq", set_vhf_freq)],
)

vhf_mode_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_mode", set_vhf_mode)],
    states={VHF_MODE: [CallbackQueryHandler(read_vhf_mode)]},
    fallbacks=[CommandHandler("set_vhf_mode", set_vhf_mode)],
)

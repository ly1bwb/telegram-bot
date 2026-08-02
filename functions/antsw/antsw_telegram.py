from functions.default import *
from functions.antsw.antsw_mqtt import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode


def antsw_label(num):
    return antsw_antennas.get(num, f"Antena {num}")


def antsw_resolve(arg):
    """Accepts an antenna number or its name, returns the number or None."""
    if arg in antsw_antennas:
        return arg
    for num, name in antsw_antennas.items():
        if name.lower() == arg.lower():
            return num
    return None


def antsw_is_enabled(num):
    """The device ignores disabled antennas, so reject them before publishing."""
    enabled = get_antsw_enabled()
    return enabled is None or num in enabled


def antsw_switch(num):
    """Publishes the new selection if it differs, returns the reply text."""
    if get_antsw_offline():
        return "⚠️ Perjungiklis neatsako, antena neperjungta"
    if not antsw_is_enabled(num):
        return f"Antena <b>{antsw_label(num)}</b> yra išjungta perjungiklyje"
    if num == get_antsw_selected():
        return f"Jau pasirinkta antena <b>{antsw_label(num)}</b>"
    change_antsw(num)
    return f"📡 Perjungiu anteną į <b>{antsw_label(num)}</b>"


def antsw_status():
    selected = get_antsw_selected()
    if selected not in antsw_antennas:
        msg = "Antenų perjungiklio būsena nežinoma"
    else:
        msg = f"📡 Pasirinkta antena: <b>{get_antsw_name() or antsw_label(selected)}</b>"
    if not get_antsw_online():
        msg += "\n⚠️ Perjungiklis neatsako"
    return msg


async def get_ant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("get_ant()", update)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        text=antsw_status(),
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def set_ant(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_ant()", update)
    username = update.message.from_user["username"]
    if not await check_permissions(username, update, context):
        return ConversationHandler.END
    if len(context.args) > 0:
        num = antsw_resolve(context.args[-1])
        msg = antsw_switch(num) if num else "Neteisingas parametras"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=msg,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END
    else:
        buttons = [
            InlineKeyboardButton(text=antsw_label(num), callback_data=num)
            for num in antsw_antennas
            if antsw_is_enabled(num)
        ]
        if not buttons:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.effective_message.message_thread_id,
                text="Perjungiklyje neįjungta nė viena antena",
            )
            return ConversationHandler.END

        options = [buttons[i : i + 2] for i in range(0, len(buttons), 2)]

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"{antsw_status()}\nPasirinkite arba įveskite naują anteną:",
            reply_markup=InlineKeyboardMarkup(options),
            parse_mode=ParseMode.HTML,
        )
        return ANTSW


async def read_ant(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_ant()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]

    if await check_permissions(username, update, context):
        num = antsw_resolve(query.data)
        msg = antsw_switch(num) if num else "Neteisingas parametras"
        await query.edit_message_text(text=msg, parse_mode=ParseMode.HTML)
    return ConversationHandler.END


antsw_handler = ConversationHandler(
    entry_points=[CommandHandler("setant", set_ant)],
    states={ANTSW: [CallbackQueryHandler(read_ant)]},
    fallbacks=[CommandHandler("setant", set_ant)],
)

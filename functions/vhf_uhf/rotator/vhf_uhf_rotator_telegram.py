from functions.default import *
from functions.vhf_uhf.rotator.vhf_uhf_rotator_mqtt import *
from functions.geo import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode


async def vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if get_vhf_rot_online():
        az = get_vhf_rot_az()
        el = get_vhf_rot_el()
        text = f"VHF antenų azimutas: {az}º, elevacija: {el}º"
    else:
        text = "VHF antenų kryptis nežinoma\n⚠️ Rotatorius neatsako"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        text=text,
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def read_vhf_az(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    if await check_permissions(username, update, context):
        change_vhf_az(query.data)
        await query.edit_message_text(
            text=f"Suku VHF antenas iš {get_vhf_rot_az()}º į {query.data}º"
        )
    return ConversationHandler.END


async def set_vhf_az(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_vhf_az()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and await check_permissions(username, update, context):
        change_vhf_az(context.args[-1])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Suku VHF antenas iš {get_vhf_rot_az()}º į {context.args[-1]}º",
        )
    else:
        options = [
            [
                InlineKeyboardButton(text="0º (N)", callback_data="0"),
                InlineKeyboardButton(text="90º (E)", callback_data="90"),
                InlineKeyboardButton(text="180º (S)", callback_data="180"),
                InlineKeyboardButton(text="270º (W)", callback_data="270"),
            ],
            [
                InlineKeyboardButton(text="Kaunas", callback_data="286"),
                InlineKeyboardButton(text="Klaipėda", callback_data="294"),
                InlineKeyboardButton(text="Šiauliai", callback_data="318"),
                InlineKeyboardButton(text="Panevėžys", callback_data="333"),
            ],
            [
                InlineKeyboardButton(text="Utena", callback_data="13"),
                InlineKeyboardButton(text="Alytus", callback_data="246"),
                InlineKeyboardButton(text="Gardinas", callback_data="220"),
                InlineKeyboardButton(text="Minskas", callback_data="121"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"🧭 Pasirinkite arba įveskite azimutą (dabar: {get_vhf_rot_az()}º):",
            reply_markup=reply_markup,
        )
        return VHF_AZ


async def read_vhf_el(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    if await check_permissions(username, update, context):
        if int(get_vhf_rot_el()) > int(query.data):
            msg = "Leidžiu"
        else:
            msg = "Keliu"
        change_vhf_el(query.data)
        await query.edit_message_text(
            text=f"{msg} VHF antenas iš {get_vhf_rot_el()}º į {query.data}º"
        )
    return ConversationHandler.END


async def set_vhf_el(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_vhf_el()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and await check_permissions(username, update, context):
        change_vhf_el(context.args[-1])
        if int(get_vhf_rot_el()) > int(context.args[-1]):
            msg = "Leidžiu"
        else:
            msg = "Keliu"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"🔭 {msg} VHF antenas iš {get_vhf_rot_el()}º į {context.args[-1]}º",
        )
    else:
        options = [
            [
                InlineKeyboardButton(text="0º", callback_data="0"),
                InlineKeyboardButton(text="30º", callback_data="30"),
                InlineKeyboardButton(text="45º", callback_data="45"),
                InlineKeyboardButton(text="90º", callback_data="90"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(options)
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"🔭 Pasirinkite arba įveskite elevaciją (dabar: {get_vhf_rot_el()}º):",
            reply_markup=reply_markup,
        )
        return VHF_EL


async def get_moon_vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("get_moon_vhf_azel()", update)
    m_az, m_el = get_moon_azel(home_qth)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        text=f"Mėnulis 🌕 dabar yra {m_az}º azimute, {m_el}º elevacijoje",
    )
    return ConversationHandler.END


async def set_moon_vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("set_moon_vhf_azel()", update)
    username = update.message.from_user["username"]
    if await check_permissions(username, update, context):
        m_az, m_el = get_moon_azel(home_qth)
        if m_el >= 0:
            change_vhf_az(m_az)
            change_vhf_el(m_el)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.effective_message.message_thread_id,
                text=f"Suku į Mėnulį 🌕 iš {get_vhf_rot_az()}º, {get_vhf_rot_el()}º į {m_az}º, {m_el}º",
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                message_thread_id=update.effective_message.message_thread_id,
                text=f"Mėnulis 🌕 dabar po horizontu {m_el}º",
            )
    return ConversationHandler.END


vhf_az_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_az", set_vhf_az)],
    states={VHF_AZ: [CallbackQueryHandler(read_vhf_az)]},
    fallbacks=[CommandHandler("set_vhf_az", set_vhf_az)],
)

vhf_el_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_el", set_vhf_el)],
    states={VHF_EL: [CallbackQueryHandler(read_vhf_el)]},
    fallbacks=[CommandHandler("set_vhf_el", set_vhf_el)],
)

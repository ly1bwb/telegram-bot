from functions.default import *
from functions.hf.rotator.hf_rotator_mqtt import *
from functions.geo import *
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ConversationHandler
from telegram.constants import ParseMode


async def hf_az(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    az = get_hf_rot_az()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        text=f"HF antenų azimutas: {az}º",
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


async def read_hf_az(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    if check_permissions(username, update, context):
        change_hf_az(query.data)
        await query.edit_message_text(
            text=f"Suku HF antenas iš {get_hf_rot_az()}º į {query.data}º"
        )
    return ConversationHandler.END


async def set_hf_az(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_hf_az()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_hf_az(context.args[-1])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            message_thread_id=update.effective_message.message_thread_id,
            text=f"Suku HF antenas iš {get_hf_rot_az()}º į {context.args[-1]}º",
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
            text=f"🧭 Pasirinkite arba įveskite azimutą (dabar: {get_hf_rot_az()}º):",
            reply_markup=reply_markup,
        )
        return HF_AZ


hf_az_handler = ConversationHandler(
    entry_points=[CommandHandler("set_hf_az", set_hf_az)],
    states={HF_AZ: [CallbackQueryHandler(read_hf_az)]},
    fallbacks=[CommandHandler("set_hf_az", set_hf_az)],
)

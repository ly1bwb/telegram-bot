import os
import socket
import asyncio
import telegram

import paho.mqtt.client as mqtt

from dotenv import load_dotenv
from telegram import InlineKeyboardMarkup, InlineKeyboardButton, Update
from telegram.constants import (
    ParseMode,
    ChatAction,
)
from telegram.ext import (
    Application,
    filters,
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    ApplicationBuilder,
)
from threading import Thread

from settings import *
from functions.default import *
from functions.camera import *
from functions.geo import *

load_dotenv()

VERSION = "1.3.0"

bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
application = ApplicationBuilder().token(bot_token).build()
default_chat_id = os.environ.get("TELEGRAM_CHAT_ID")

CAM, FREQ, AZ, EL, MODE, SDR_STAT, MONITORS = range(7)


def mqtt_rotator_loop():
    mqtt_loop(mqtt_vhf_rot_path + "/#", read_mqtt_rotator_azel)


def mqtt_radio_loop():
    mqtt_loop(mqtt_radio_path + "/#", read_mqtt_vhf_freq)


def mqtt_vhf_sdr_loop():
    mqtt_loop("stat/tasmota_E65E89/#", read_mqtt_vhf_sdr_state)


def mqtt_monitors_loop():
    mqtt_loop("stat/tasmota_050E88/#", read_mqtt_monitors_state)


def mqtt_loop(topic, handler):
    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_host, 1883, 60)
    log.info("Connected to MQTT")
    mqtt_client.on_message = handler
    mqtt_client.subscribe(topic)
    log.info(f"Subscribed to MQTT: {topic}")
    mqtt_client.loop_forever()


def read_mqtt_rotator_azel(client, userdata, message):
    global vhf_rot_az
    global vhf_rot_el
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_vhf_rot_path + "/azimuth":
        vhf_rot_az = payload_value
    if message.topic == mqtt_vhf_rot_path + "/elevation":
        vhf_rot_el = payload_value
    if message.topic == mqtt_vhf_rot_path + "/direction":
        pass


def read_mqtt_vhf_freq(client, userdata, message):
    global vhf_rig_freq
    global vhf_rig_mode
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_radio_path + "/frequency":
        vhf_rig_freq = payload_value
    if message.topic == mqtt_radio_path + "/mode":
        vhf_rig_mode = payload_value


def read_mqtt_vhf_sdr_state(client, userdata, message):
    global vhf_sdr_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/tasmota_E65E89/POWER1":
        if vhf_sdr_state != payload_value:
            if payload_value == "ON":
                msg = "Įjungtas"
            else:
                msg = "Išjungtas"
            asyncio.run(send_mqtt_state_to_telegram(f"📻 SDR MFJ VHF Switch {msg}", default_chat_id))
        vhf_sdr_state = payload_value


def read_mqtt_monitors_state(client, userdata, message):
    global monitors_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/tasmota_050E88/POWER":
        if monitors_state != payload_value:
            if payload_value == "ON":
                msg = "Įjungti"
            else:
                msg = "Išjungti"
            
            # For running on Windows
            # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            asyncio.run(send_mqtt_state_to_telegram(f"🖥️ Monitoriai {msg}", default_chat_id))

            # alternative method, just for reference
            # loop = asyncio.new_event_loop()
            # loop.run_until_complete(send_mqtt_state_to_telegram(f"🖥️ Monitoriai {msg}", default_chat_id))
            # loop.close()
        monitors_state = payload_value

async def send_mqtt_state_to_telegram(text, chatid):
    app = ApplicationBuilder().token(bot_token).build()
    await app.bot.send_message(chat_id=chatid, text=text)

    # alternative method, maybe simpler
    # await telegram.Bot(bot_token).send_message(
    #     chat_id=chatid,
    #     text=text,
    # )

async def set_vhf_az(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_vhf_az()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_az(context.args[-1])
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Suku VHF antenas iš {vhf_rot_az}º į {context.args[-1]}º",
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
            text=f"🧭 Pasirinkite arba įveskite azimutą (dabar: {vhf_rot_az}º):",
            reply_markup=reply_markup,
        )
        return AZ


async def set_vhf_el(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_func("set_vhf_el()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_el(context.args[-1])
        if vhf_rot_el > context.args[-1]:
            msg = "Leidžiu"
        else:
            msg = "Keliu"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🔭 {msg} VHF antenas iš {vhf_rot_el}º į {context.args[-1]}º",
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
            text=f"🔭 Pasirinkite arba įveskite elevaciją (dabar: {vhf_rot_el}º):",
            reply_markup=reply_markup,
        )
        return EL


async def set_moon_vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("set_moon_vhf_azel()", update)
    username = update.message.from_user["username"]
    if check_permissions(username, update, context):
        m_az, m_el = get_moon_azel(home_qth)
        if m_el >= 0:
            change_az(m_az)
            change_el(m_el)
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Suku į Mėnulį 🌕 iš {vhf_rot_az}º, {vhf_rot_el}º į {m_az}º, {m_el}º",
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"Mėnulis 🌕 dabar po horizontu {m_el}º",
            )
    return ConversationHandler.END


async def get_moon_vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("get_moon_vhf_azel()", update)
    m_az, m_el = get_moon_azel(home_qth)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Mėnulis 🌕 dabar yra {m_az}º azimute, {m_el}º elevacijoje",
    )
    return ConversationHandler.END


def check_permissions(username, update, context):
    if username in valid_users:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Neturite tokių teisių.",
        )
        return False


async def read_vhf_az(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    if check_permissions(username, update, context):
        change_az(query.data)
        await query.edit_message_text(
            text=f"Suku VHF antenas iš {vhf_rot_az}º į {query.data}º"
        )
    return ConversationHandler.END


async def read_vhf_el(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    if check_permissions(username, update, context):
        if vhf_rot_el > query.data:
            msg = "Leidžiu"
        else:
            msg = "Keliu"
        change_el(query.data)
        await query.edit_message_text(
            text=f"{msg} VHF antenas iš {vhf_rot_el}º į {query.data}º"
        )
    return ConversationHandler.END

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

def change_az(degrees):
    _mqtt_publish(mqtt_vhf_rot_path + "/set/azimuth", degrees)
    return


def change_el(degrees):
    if int(degrees) >= 0 and int(degrees) < 360:
        _mqtt_publish(mqtt_vhf_rot_path + "/set/elevation", degrees)
    log.info("change_el({})".format(degrees))
    return


def change_freq(freq):
    _mqtt_publish(mqtt_radio_path + "/set/frequency", freq)
    return


def change_mode(mode):
    _mqtt_publish(mqtt_radio_path + "/set/mode", mode)
    return


def change_vhf_sdr_state(state):
    _mqtt_publish("cmnd/tasmota_E65E89/POWER1", state)
    return


def change_monitors_state(state):
    _mqtt_publish("cmnd/tasmota_050E88/POWER1", state)
    return


def _mqtt_publish(topic, message):
    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_host, 1883, 60)
    log.info("Connected publisher to MQTT")
    mqtt_client.publish(topic, message)
    log.debug(f"Published {message} to {topic}")
    mqtt_client.disconnect()
    log.info("Disconnected publisher from MQTT (this is OK)")
    return


async def set_vhf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Called set_vhf_mode() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_mode(context.args[-1])
        f1 = vhf_rig_mode
        f2 = context.args[-1]
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Keičiu režimą iš {f1} į {f2}"
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
            text=f"Pasirinkite režimą (dabar {vhf_rig_mode}):",
            reply_markup=reply_markup,
        )
        return MODE


async def read_vhf_mode(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_mode()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    f1 = vhf_rig_mode
    f2 = query.data
    if check_permissions(username, update, context):
        change_mode(query.data)
        await query.edit_message_text(text=f"Keičiu režimą iš {f1} į {f2}")
    return ConversationHandler.END


async def set_vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"Called set_vhf_freq() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_freq(context.args[-1])
        f1 = _format_frequency(vhf_rig_freq)
        f2 = _format_frequency(context.args[-1])
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"Keičiu dažnį iš {f1} į {f2}"
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
            text="Pasirinkite arba įveskite dažnį:",
            reply_markup=reply_markup,
        )
        return FREQ


async def read_vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_freq()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]
    f1 = _format_frequency(vhf_rig_freq)
    f2 = _format_frequency(query.data)
    if check_permissions(username, update, context):
        change_freq(query.data)
        await query.edit_message_text(text=f"Keičiu dažnį iš {f1} į {f2}")
    return ConversationHandler.END


async def vhf_azel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    az = vhf_rot_az
    el = vhf_rot_el
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"VHF antenų azimutas: {az}º, elevacija: {el}º",
        parse_mode=ParseMode.HTML,
    )
    return ConversationHandler.END


def _format_frequency(f):
    return f[-9] + f[-8] + f[-7] + "." + f[-6] + f[-5] + f[-4] + " MHz"


async def vhf_freq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    ff = _format_frequency(vhf_rig_freq)
    msg = (
        "VHF stoties dažnis: \n<b>"
        + ff
        + " ("
        + vhf_rig_mode
        + ")</b>"
        + "\n👉 <a href='http://sdr.vhf.lt:8000/ft847'>Klausyti gyvai</a>"
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END

async def set_vhf_sdr_switch_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called set_vhf_sdr_switch_state() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        new_state = context.args[-1].upper()

        if new_state == "ON" or new_state == "OFF":
            if new_state != vhf_sdr_state:
                msg = (
                    "Perjungiu VHF MFJ Switch state iš <b>"
                    + vhf_sdr_state
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
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Dabar MFJ VHF Switch yra <b>{vhf_sdr_state}</b>\nPasirinkite arba įveskite naują MFJ Switch būseną:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.HTML,
        )
    return SDR_STAT

async def read_vhf_sdr_switch_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called read_vhf_sdr_switch_state()")
    query = update.callback_query
    await query.answer()
    username = query.from_user["username"]

    if check_permissions(username, update, context):
        new_state = query.data.upper()
        old_state = vhf_sdr_state

        if new_state == "ON" or new_state == "OFF":
            if new_state != old_state:
                msg = (
                    "Perjungiu MFJ VHF Switch state iš <b>"
                    + vhf_sdr_state
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
                chat_id=update.effective_chat.id, text=f"Neteisingas parametras"
            )
    return ConversationHandler.END

async def set_monitors_state(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log.info(f"Called set_monitors_state() by {update.message.from_user['username']}")
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        new_state = context.args[-1].upper()

        if new_state == "ON" or new_state == "OFF":
            if new_state != monitors_state:
                msg_action = "Įjungiu" if new_state == "ON" else "Išjungiu"
                msg = (
                    f"{msg_action} monitorius"
                )
                change_monitors_state(new_state)
            else:
                if monitors_state == "ON":
                    msg_action = "Įjungti"
                elif monitors_state == "OFF":
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
        
        if monitors_state == "ON":
            msg_action = "Įjungti"
        elif monitors_state == "OFF":
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
        old_state = monitors_state

        if new_state == "ON" or new_state == "OFF":
            if new_state != old_state:
                msg_state = "Įjungiu" if new_state == "ON" else "Išjungiu"
                msg = (
                    f"{msg_state} monitorius"
                )
                change_monitors_state(new_state)
            else:
                if monitors_state == "ON":
                    msg_action = "Įjungti"
                elif monitors_state == "OFF":
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

async def calculate_azimuth_by_loc(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.message.from_user["id"]
    loc = update.message.text
    deg, dist = angle_distance_qth(loc)
    deg = round(deg)
    dist = round(dist / 1000)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"Azimutas į {loc} yra {deg}° (atstumas: {dist} km)",
    )
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text=f"/set_vhf_az {deg}"
    )
    return ConversationHandler.END


vhf_freq_handler = ConversationHandler(
    entry_points=[
        CommandHandler("set_vhf_freq", set_vhf_freq),
    ],
    states={
        FREQ: [CallbackQueryHandler(read_vhf_freq)],
    },
    fallbacks=[CommandHandler("set_vhf_freq", set_vhf_freq)],
)


vhf_az_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_az", set_vhf_az)],
    states={AZ: [CallbackQueryHandler(read_vhf_az)]},
    fallbacks=[CommandHandler("set_vhf_az", set_vhf_az)],
)

vhf_el_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_el", set_vhf_el)],
    states={EL: [CallbackQueryHandler(read_vhf_el)]},
    fallbacks=[CommandHandler("set_vhf_el", set_vhf_el)],
)

vhf_mode_handler = ConversationHandler(
    entry_points=[CommandHandler("set_vhf_mode", set_vhf_mode)],
    states={MODE: [CallbackQueryHandler(read_vhf_mode)]},
    fallbacks=[CommandHandler("set_vhf_mode", set_vhf_mode)],
)

vhf_sdr_state_handler = ConversationHandler(
    entry_points=[CommandHandler("vhf_sdr", set_vhf_sdr_switch_state)],
    states={SDR_STAT: [CallbackQueryHandler(read_vhf_sdr_switch_state)]},
    fallbacks=[CommandHandler("vhf_sdr", set_vhf_sdr_switch_state)],
)

monitors_state_handler = ConversationHandler(
    entry_points=[CommandHandler("monitors", set_monitors_state)],
    states={MONITORS: [CallbackQueryHandler(read_monitors_state)]},
    fallbacks=[CommandHandler("monitors", set_monitors_state)],
)

application.add_handler(CommandHandler("start", start))

application.add_handler(CommandHandler("roof_camera", roof_camera))

application.add_handler(CommandHandler("rig_camera", rig_camera))

application.add_handler(CommandHandler("lower_camera", lower_camera))

application.add_handler(CommandHandler("window_camera", window_camera))

application.add_handler(CommandHandler("main_camera", main_camera))

application.add_handler(CommandHandler("vhf_freq", vhf_freq))

application.add_handler(CommandHandler("vhf_azel", vhf_azel))

application.add_handler(CommandHandler("moon", get_moon_vhf_azel))

application.add_handler(CommandHandler("moon_azel", set_moon_vhf_azel))

application.add_handler(CommandHandler("sveiki", sveiki))

application.add_handler(CommandHandler("status", get_status))

application.add_handler(vhf_freq_handler)

application.add_handler(vhf_az_handler)

application.add_handler(vhf_el_handler)

application.add_handler(vhf_mode_handler)

application.add_handler(vhf_sdr_state_handler)

application.add_handler(monitors_state_handler)

application.add_handler(
    MessageHandler(
        filters.Regex(
            r"^\w{2}\d{2}\w{2}(\d\d){0,1}$",
        ),
        calculate_azimuth_by_loc,
    )
)

if __name__ == "__main__":
    mqtt_rig_thread = Thread(target=mqtt_radio_loop)
    mqtt_rig_thread.start()
    mqtt_rot_thread = Thread(target=mqtt_rotator_loop)
    mqtt_rot_thread.start()
    mqtt_vhf_sdr_thread = Thread(target=mqtt_vhf_sdr_loop)
    mqtt_vhf_sdr_thread.start()
    mqtt_monitors_thread = Thread(target=mqtt_monitors_loop)
    mqtt_monitors_thread.start()
    # Telegram thread must be last
    telegram_thread = Thread(target=application.run_polling(allowed_updates=Update.ALL_TYPES))
    telegram_thread.start()

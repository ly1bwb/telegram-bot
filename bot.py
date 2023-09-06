import os
import time
import math
import ephem
import pyproj
import maidenhead as mh
import logging
import datetime
import urllib.request

import paho.mqtt.client as mqtt

from math import pi
from html.parser import HTMLParser
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
)
from threading import Thread

load_dotenv()

application = Application.builder().token(os.environ.get("TELEGRAM_BOT_TOKEN")).build()

start_text = "Labas - aš esu LY1BWB stoties botas."
roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"

lower_camera_url = "http://192.168.42.10/webcam/webcam3.jpg"
rig_camera_url = "http://192.168.42.10/webcam/webcam1.jpg"
window_camera_url = "http://192.168.42.129/snapshot.jpg?"
main_camera_url = (
    "http://192.168.42.183/onvifsnapshot/media_service/snapshot?channel=1&subtype=0"
)

mqtt_host = "mqtt.vurk"
vhf_rig_freq = "000000000"
vhf_rig_mode = "FT8"

vhf_rot_az = 0
vhf_rot_el = 0

CAM, FREQ, AZ, EL, MODE = range(5)

valid_users = {
    "LY2EN",
    "sutemos",
    "LY1LB",
    "LY0NAS",
    "LY5AT",
    "LY1WS",
    "LY2DC",
    "LY1JA",
    "LY4AU",
    "volwerene"
}

home_qth = "KO24PR15"

log = logging
log.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


class webcam_parser(HTMLParser):
    roof_camera_img = ""

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.roof_camera_img = roof_camera_host + attrs[0][1]
            logging.info("Found IMG: " + self.roof_camera_img)


def log_func(name, update):
    log.info(f"Called {name} by {update.message.from_user['username']}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)
    return ConversationHandler.END


def angle_between_loc(x1, y1, x2, y2):
    geodesic = pyproj.Geod(ellps="WGS84")
    fwd_azimuth, _back_azimuth, distance = geodesic.inv(y1, x1, y2, x2)
    return fwd_azimuth + 180, distance


def angle_distance_qth(loc_qth):
    (x1, y1) = mh.to_location(loc_qth)
    (x2, y2) = mh.to_location(home_qth)
    return angle_between_loc(x1, y1, x2, y2)


def get_moon_azel(qth):
    home = ephem.Observer()
    _lat, _lon = mh.to_location(qth)
    home.lat = str(_lat)
    home.lon = str(_lon)
    home.date = datetime.datetime.utcnow()
    moon = ephem.Moon()
    moon.compute(home)
    return int(moon.az / pi * 180), int(moon.alt / pi * 180)


async def lower_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("lower_camera()", update)
    web_file = urllib.request.urlopen(lower_camera_url)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())
    return ConversationHandler.END


async def rig_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("rig_camera()", update)
    web_file = urllib.request.urlopen(rig_camera_url)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())
    return ConversationHandler.END

async def window_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("window)camera()", update)
    web_file = urllib.request.urlopen(window_camera_url, timeout=5)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())
    return ConversationHandler.END

async def main_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("main_camera()", update)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    web_file = urllib.request.urlopen(main_camera_url)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())
    return ConversationHandler.END


async def roof_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("roof_camera()", update)
    #await update._bot.send_chat_action(
    #    chat_id=update.effective_chat.id, action=ChatAction.TYPING
    #)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))
    web_file = urllib.request.urlopen(parser.roof_camera_img)
    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def mqtt_rotator_loop():
    mqtt_loop("VURK/rotator/vhf/#", read_mqtt_rotator_azel)


def mqtt_radio_loop():
    mqtt_loop("VURK/radio/IC9700/#", read_mqtt_vhf_freq)


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
    if message.topic == "VURK/rotator/vhf/azimuth":
        vhf_rot_az = payload_value
    if message.topic == "VURK/rotator/vhf/elevation":
        vhf_rot_el = payload_value
    if message.topic == "VURK/rotator/vhf/direction":
        pass


def read_mqtt_vhf_freq(client, userdata, message):
    global vhf_rig_freq
    global vhf_rig_mode
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "VURK/radio/IC9700/frequency":
        vhf_rig_freq = payload_value
    if message.topic == "VURK/radio/IC9700/mode":
        vhf_rig_mode = payload_value


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
    user = update.message.from_user
    log_func("sveiki()", update)
    #await update.message.reply_text("Sveiki")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Sveiki")
    return ConversationHandler.END

def change_az(degrees):
    _mqtt_publish("VURK/rotator/vhf/set/azimuth", degrees)
    return


def change_el(degrees):
    if int(degrees) >= 0 and int(degrees) < 360:
        _mqtt_publish("VURK/rotator/vhf/set/elevation", degrees)
    log.info("change_el({})".format(degrees))
    return


def change_freq(freq):
    _mqtt_publish("VURK/radio/IC9700/set/frequency", freq)
    return


def change_mode(mode):
    _mqtt_publish("VURK/radio/IC9700/set/mode", mode)
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

application.add_handler(vhf_freq_handler)

application.add_handler(vhf_az_handler)

application.add_handler(vhf_el_handler)

application.add_handler(vhf_mode_handler)

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
    # Telegram thread must be last
    telegram_thread = Thread(target=application.run_polling(allowed_updates=Update.ALL_TYPES))
    telegram_thread.start()

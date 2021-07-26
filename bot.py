import os
import time
import logging
import urllib.request

import paho.mqtt.client as mqtt

from html.parser import HTMLParser
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton, ChatAction
from threading import Thread

load_dotenv()
updater = Updater(token=os.environ.get("TELEGRAM_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

start_text = "Labas - aš esu LY1BWB stoties botas."
roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"

lower_camera_url = "http://192.168.42.10/webcam/webcam3.jpg"
main_camera_url = (
    "http://192.168.42.183/onvifsnapshot/media_service/snapshot?channel=1&subtype=0"
)

mqtt_host = "192.168.42.253"
vhf_rig_freq = "000000000"
vhf_rig_mode = "FT8"

vhf_rot_az = 0
vhf_rot_el = 0

CAM, FREQ, AZ, EL = range(4)

valid_users = {
    "LY2EN",
    "sutemos",
    "LY1LB",
    "LY0NAS",
    "LY5AT",
    "LY1WS",
    "LY2DC",
    "LY1JA",
}

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


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)


def lower_camera(update, context):
    log_func("lower_camera()", update)
    web_file = urllib.request.urlopen(lower_camera_url)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def main_camera(update, context):
    log_func("main_camera()", update)
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    web_file = urllib.request.urlopen(main_camera_url)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def roof_camera(update, context):
    log_func("roof_camera()", update)
    context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))
    web_file = urllib.request.urlopen(parser.roof_camera_img)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def mqtt_rotator_loop():
    mqtt_loop("VURK/rotator/vhf/#", read_mqtt_rotator_azel)


def mqtt_radio_loop():
    mqtt_loop("VURK/radio/FT847/#", read_mqtt_vhf_freq)


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
    if message.topic == "VURK/radio/FT847/frequency":
        vhf_rig_freq = payload_value
    if message.topic == "VURK/radio/FT847/mode":
        vhf_rig_mode = payload_value


def set_vhf_az(update, context):
    log_func("set_vhf_az()", update)
    username = update.message.from_user["username"]
    if len(context.args) > 0 and check_permissions(username, update, context):
        change_az(context.args[-1])
        context.bot.send_message(
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
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Pasirinkite arba įveskite azimutą (dabar: {vhf_rot_az}º):",
            reply_markup=reply_markup,
        )
        return AZ


def check_permissions(username, update, context):
    if username in valid_users:
        return True
    else:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Neturite tokių teisių.",
        )
        return False


def read_vhf_az(update, context):
    query = update.callback_query
    query.answer()
    username = query.from_user["username"]
    if check_permissions(username, update, context):
        change_az(query.data)
        query.edit_message_text(
            text=f"Suku VHF antenas iš {vhf_rot_az}º į {query.data}º"
        )
    return


def change_az(degrees):
    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_host, 1883, 60)
    log.info("Connected publisher to MQTT")
    mqtt_client.publish("VURK/rotator/vhf/set/azimuth", degrees)
    mqtt_client.disconnect()
    log.info("Disconnected publisher from MQTT (this is OK)")
    return


def set_vhf_freq(update, context):
    log.info(f"Called set_vhf_freq() by {update.message.from_user['username']}")
    if len(context.args) > 0:
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Dar neimplementuota: " + context.args[-1],
        )
    else:
        options = [
            [
                InlineKeyboardButton(text="144,050", callback_data="144050000"),
                InlineKeyboardButton(text="144,300", callback_data="144300000"),
                InlineKeyboardButton(text="144,800", callback_data="144800000"),
            ],
            [
                InlineKeyboardButton(text="145,500", callback_data="145500000"),
                InlineKeyboardButton(text="145,800", callback_data="145800000"),
                InlineKeyboardButton(text="145,825", callback_data="145825000"),
            ],
        ]
        reply_markup = InlineKeyboardMarkup(options)
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Pasirinkite arba įveskite dažnį:",
            reply_markup=reply_markup,
        )
        return FREQ


def read_vhf_freq(update, context):
    log.info(f"Called read_vhf_freq()")
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Dar neimplementuota: {query.data}")
    return


def vhf_az(update, context):
    az = vhf_rot_az
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"VHF antenų azimutas yra {az}º.",
        parse_mode=ParseMode.HTML,
    )


def vhf_freq(update, context):
    f = vhf_rig_freq
    ff = f[-9] + f[-8] + f[-7] + "," + f[-6] + f[-5] + f[-4] + " MHz"
    msg = (
        "VHF stoties dažnis: \n<b>"
        + ff
        + " ("
        + vhf_rig_mode
        + ")</b>"
        + "\n👉 <a href='http://sdr.vhf.lt:8000/ft847'>Klausyti gyvai</a>"
    )
    context.bot.send_message(
        chat_id=update.effective_chat.id, text=msg, parse_mode=ParseMode.HTML
    )


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

dispatcher.add_handler(CommandHandler("start", start))

dispatcher.add_handler(CommandHandler("roof_camera", roof_camera))

dispatcher.add_handler(CommandHandler("lower_camera", lower_camera))

dispatcher.add_handler(CommandHandler("main_camera", main_camera))

dispatcher.add_handler(CommandHandler("vhf_freq", vhf_freq))

dispatcher.add_handler(CommandHandler("vhf_az", vhf_az))

dispatcher.add_handler(vhf_freq_handler)

dispatcher.add_handler(vhf_az_handler)

if __name__ == "__main__":
    telegram_thread = Thread(target=updater.start_polling)
    telegram_thread.start()
    mqtt_rig_thread = Thread(target=mqtt_radio_loop)
    mqtt_rig_thread.start()
    mqtt_rot_thread = Thread(target=mqtt_rotator_loop)
    mqtt_rot_thread.start()

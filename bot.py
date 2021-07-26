import os
import time
import logging
import urllib.request

import paho.mqtt.client as mqtt

from html.parser import HTMLParser
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram.ext import CommandHandler, CallbackQueryHandler
from telegram import ParseMode, InlineKeyboardMarkup, InlineKeyboardButton
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
    web_file = urllib.request.urlopen(main_camera_url)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def roof_camera(update, context):
    log_func("roof_camera()", update)
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))
    web_file = urllib.request.urlopen(parser.roof_camera_img)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def mqtt_freq_loop():
    mqtt_client = mqtt.Client()
    mqtt_client.connect(mqtt_host, 1883, 60)
    log.info("Connected to MQTT")
    mqtt_client.on_message = read_mqtt_vhf_freq
    mqtt_client.subscribe("VURK/radio/FT847/#")
    mqtt_client.loop_forever()


def read_mqtt_vhf_freq(client, userdata, message):
    global vhf_rig_freq
    global vhf_rig_mode
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "VURK/radio/FT847/frequency":
        vhf_rig_freq = payload_value
    if message.topic == "VURK/radio/FT847/mode":
        vhf_rig_mode = payload_value


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


def read_vhf_freq(update, context):
    log.info(f"Called read_vhf_freq()")
    query = update.callback_query
    query.answer()
    query.edit_message_text(text=f"Dar neimplementuota: {query.data}")


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


)

dispatcher.add_handler(CommandHandler("start", start))

dispatcher.add_handler(CommandHandler("roof_camera", roof_camera))

dispatcher.add_handler(CommandHandler("lower_camera", lower_camera))

dispatcher.add_handler(CommandHandler("main_camera", main_camera))

dispatcher.add_handler(CommandHandler("vhf_freq", vhf_freq))

dispatcher.add_handler(CommandHandler("set_vhf_freq", set_vhf_freq))

dispatcher.add_handler(CallbackQueryHandler(read_vhf_freq))

if __name__ == "__main__":
    telegram_thread = Thread(target=updater.start_polling)
    telegram_thread.start()
    mqtt_thread = Thread(target=mqtt_freq_loop)
    mqtt_thread.start()

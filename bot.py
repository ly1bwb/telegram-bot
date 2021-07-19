import os
import time
import logging
import urllib.request

import paho.mqtt.client as mqtt

from html.parser import HTMLParser
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram.ext import CommandHandler
from threading import Thread

load_dotenv()
updater = Updater(token=os.environ.get("TELEGRAM_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

start_text = "Labas - aš esu LY1BWB stoties botas."
roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"

lower_camera_url = "http://192.168.42.10/webcam/webcam3.jpg"

mqtt_host = "192.168.42.253"
vhf_rig_freq = "not yet defined"


class webcam_parser(HTMLParser):
    roof_camera_img = ""

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.roof_camera_img = roof_camera_host + attrs[0][1]
            logging.info("Found IMG: " + self.roof_camera_img)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)


def lower_camera(update, context):
    web_file = urllib.request.urlopen(lower_camera_url)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def roof_camera(update, context):
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))
    web_file = urllib.request.urlopen(parser.roof_camera_img)
    context.bot.send_photo(chat_id=update.effective_chat.id, photo=web_file.read())


def mqtt_freq_loop():
    mqtt_client = mqtt.Client()
    logging.info("Connecting to MQTT...")
    mqtt_client.connect(mqtt_host, 1883, 60)
    mqtt_client.on_message = read_mqtt_vhf_freq
    mqtt_client.subscribe("VURK/radio/FT847/frequency")
    mqtt_client.loop_forever()


def read_mqtt_vhf_freq(client, userdata, message):
    global vhf_rig_freq
    vhf_rig_freq = str(message.payload.decode("utf-8"))
    logging.info("MQTT thread: VHF freq: " + vhf_rig_freq)


def vhf_freq(update, context):
    msg = "VHF rig frequency is " + vhf_rig_freq
    context.bot.send_message(chat_id=update.effective_chat.id, text=msg)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

dispatcher.add_handler(CommandHandler("start", start))

dispatcher.add_handler(CommandHandler("roof_camera", roof_camera))

dispatcher.add_handler(CommandHandler("lower_camera", lower_camera))

dispatcher.add_handler(CommandHandler("vhf_freq", vhf_freq))

if __name__ == "__main__":
    telegram_thread = Thread(target=updater.start_polling)
    telegram_thread.start()
    mqtt_thread = Thread(target=mqtt_freq_loop)
    mqtt_thread.start()

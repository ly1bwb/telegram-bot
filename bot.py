import os
import time
import logging
import urllib.request

from html.parser import HTMLParser
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram.ext import CommandHandler

load_dotenv()
updater = Updater(token=os.environ.get("TELEGRAM_BOT_TOKEN"), use_context=True)
dispatcher = updater.dispatcher

start_text = "Labas - aš esu LY1BWB stoties botas."
roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"


class webcam_parser(HTMLParser):
    roof_camera_img = ""

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.roof_camera_img = roof_camera_host + attrs[0][1]
            logging.info("Found IMG: " + self.roof_camera_img)


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text=start_text)


def roof_camera(update, context):
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))

    web_file = urllib.request.urlopen(parser.roof_camera_img)
    context.bot.send_photo(
        chat_id=update.effective_chat.id, photo=web_file.read()
    )


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

start_handler = CommandHandler("start", start)
dispatcher.add_handler(start_handler)

camera_handler = CommandHandler("roof_camera", roof_camera)
dispatcher.add_handler(camera_handler)

updater.start_polling()

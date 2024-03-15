from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ChatAction

import urllib.request
from html.parser import HTMLParser

from settings import *

from functions.default import *


class webcam_parser(HTMLParser):
    roof_camera_img = ""

    def handle_startendtag(self, tag, attrs):
        if tag == "img":
            self.roof_camera_img = roof_camera_host + attrs[0][1]
            logging.info("Found IMG: " + self.roof_camera_img)


async def lower_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("lower_camera()", update)
    web_file = urllib.request.urlopen(lower_camera_url)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        photo=web_file.read(),
    )
    return ConversationHandler.END


async def rig_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("rig_camera()", update)
    web_file = urllib.request.urlopen(rig_camera_url)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        photo=web_file.read(),
    )
    return ConversationHandler.END


async def window_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("window)camera()", update)
    web_file = urllib.request.urlopen(window_camera_url, timeout=5)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        photo=web_file.read(),
    )
    return ConversationHandler.END


async def main_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("main_camera()", update)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        action=ChatAction.TYPING,
    )
    web_file = urllib.request.urlopen(main_camera_url)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        photo=web_file.read(),
    )
    return ConversationHandler.END


async def roof_camera(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_func("roof_camera()", update)
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        action=ChatAction.TYPING,
    )
    web_cam_url = urllib.request.urlopen(roof_camera_url)
    web_cam_html = web_cam_url.read()
    parser = webcam_parser()
    parser.feed(web_cam_html.decode("utf-8"))
    web_file = urllib.request.urlopen(parser.roof_camera_img)
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        message_thread_id=update.effective_message.message_thread_id,
        photo=web_file.read(),
    )

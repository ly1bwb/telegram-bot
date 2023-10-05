import ephem
import pyproj
import datetime
from math import pi

from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import maidenhead as mh

from settings import *

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

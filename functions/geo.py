import ephem
import pyproj
import datetime
from math import pi

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
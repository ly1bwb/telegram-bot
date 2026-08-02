from functions.default import *
from common.mqtt import *

antsw_selected = "n/a"
antsw_name = ""
antsw_lwt = "n/a"
# None = device did not report it, treat every antenna as available.
antsw_enabled = None


def mqtt_antsw_loop():
    mqtt_loop(mqtt_antsw_path + "/status/#", read_mqtt_antsw_state)


def change_antsw(antenna):
    mqtt_publish(mqtt_antsw_path + "/set", antenna)
    return


def read_mqtt_antsw_state(client, userdata, message):
    global antsw_selected
    global antsw_name
    global antsw_lwt
    global antsw_enabled
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_antsw_path + "/status/selected":
        antsw_selected = payload_value
    if message.topic == mqtt_antsw_path + "/status/name":
        antsw_name = payload_value
    if message.topic == mqtt_antsw_path + "/status/LWT":
        antsw_lwt = payload_value
    if message.topic == mqtt_antsw_path + "/status/enabled":
        antsw_enabled = [n.strip() for n in payload_value.split(",") if n.strip()]


def get_antsw_selected():
    return antsw_selected


def get_antsw_name():
    return antsw_name


def get_antsw_enabled():
    return antsw_enabled


def get_antsw_online():
    return antsw_lwt == "Online"


def get_antsw_offline():
    return antsw_lwt == "Offline"

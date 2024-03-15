from functions.default import *
from common.mqtt import *

vhf_rig_freq = "000000000"
vhf_rig_mode = "FT8"


def mqtt_vhf_radio_loop():
    mqtt_loop(mqtt_vhf_radio_path + "/#", read_mqtt_vhf_freq)


def change_vhf_freq(freq):
    mqtt_publish(mqtt_vhf_radio_path + "/set/frequency", freq)
    return


def change_vhf_mode(mode):
    mqtt_publish(mqtt_vhf_radio_path + "/set/mode", mode)
    return


def read_mqtt_vhf_freq(client, userdata, message):
    global vhf_rig_freq
    global vhf_rig_mode
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_vhf_radio_path + "/frequency":
        vhf_rig_freq = payload_value
    if message.topic == mqtt_vhf_radio_path + "/mode":
        vhf_rig_mode = payload_value


def get_vhf_rig_freq():
    return vhf_rig_freq


def get_vhf_rig_mode():
    return vhf_rig_mode

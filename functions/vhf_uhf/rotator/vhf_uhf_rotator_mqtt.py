from functions.default import *
from common.mqtt import *

vhf_rot_az = 0
vhf_rot_el = 0

def mqtt_rotator_loop():
    mqtt_loop(mqtt_vhf_rot_path + "/#", read_mqtt_rotator_azel)

def change_az(degrees):
    mqtt_publish(mqtt_vhf_rot_path + "/set/azimuth", degrees)
    return

def change_el(degrees):
    if int(degrees) >= 0 and int(degrees) < 360:
        mqtt_publish(mqtt_vhf_rot_path + "/set/elevation", degrees)
    log.info("change_el({})".format(degrees))
    return

def read_mqtt_rotator_azel(client, userdata, message):
    global vhf_rot_az
    global vhf_rot_el
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_vhf_rot_path + "/azimuth":
        vhf_rot_az = payload_value
    if message.topic == mqtt_vhf_rot_path + "/elevation":
        vhf_rot_el = payload_value
    if message.topic == mqtt_vhf_rot_path + "/direction":
        pass

def get_vhf_rot_az():
    return vhf_rot_az

def get_vhf_rot_el():
    return vhf_rot_el

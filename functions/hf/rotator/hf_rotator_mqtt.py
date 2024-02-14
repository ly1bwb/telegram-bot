from functions.default import *
from common.mqtt import *

hf_rot_az = 0

def mqtt_hf_rotator_loop():
    mqtt_loop(mqtt_hf_rot_path + "/#", read_mqtt_hf_rotator_az)

def change_hf_az(degrees):
    mqtt_publish(mqtt_hf_rot_path + "/set/azimuth", degrees)
    return

def read_mqtt_hf_rotator_az(client, userdata, message):
    global hf_rot_az
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == mqtt_hf_rot_path + "/azimuth":
        hf_rot_az = payload_value
    if message.topic == mqtt_hf_rot_path + "/direction":
        pass

def get_hf_rot_az():
    return hf_rot_az

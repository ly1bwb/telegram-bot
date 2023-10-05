import asyncio
from functions.default import *
from common.mqtt import *

vhf_sdr_state = "n/a"

def mqtt_vhf_sdr_loop():
    mqtt_loop("stat/" + mqtt_vhf_sdr_path + "/#", read_mqtt_vhf_sdr_state)

def change_vhf_sdr_state(state):
    mqtt_publish("cmnd/" + mqtt_vhf_sdr_path + "/POWER1", state)
    return

def read_mqtt_vhf_sdr_state(client, userdata, message):
    global vhf_sdr_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/" + mqtt_vhf_sdr_path + "/POWER1":
        if vhf_sdr_state != payload_value:
            if payload_value == "ON":
                msg = "Įjungtas"
            else:
                msg = "Išjungtas"
            asyncio.run(send_mqtt_state_to_telegram(
                f"📻 SDR MFJ VHF Switch {msg}", default_chat_id))
        vhf_sdr_state = payload_value

def get_vhf_sdr_state():
    return vhf_sdr_state

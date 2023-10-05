import asyncio
from functions.default import *
from common.mqtt import *

uhf_sdr_state = "n/a"

def mqtt_uhf_sdr_loop():
    mqtt_loop("stat/" + mqtt_uhf_sdr_path + "/#", read_mqtt_uhf_sdr_state)

def change_uhf_sdr_state(state):
    mqtt_publish("cmnd/" + mqtt_uhf_sdr_path + "/POWER1", state)
    return

def read_mqtt_uhf_sdr_state(client, userdata, message):
    global uhf_sdr_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/" + mqtt_uhf_sdr_path + "/POWER1":
        if uhf_sdr_state != payload_value:
            if payload_value == "ON":
                msg = "Įjungtas"
            else:
                msg = "Išjungtas"
            asyncio.run(send_mqtt_state_to_telegram(
                f"📻 SDR MFJ UHF Switch {msg}", default_chat_id))
        uhf_sdr_state = payload_value

def get_uhf_sdr_state():
    return uhf_sdr_state

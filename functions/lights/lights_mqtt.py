import asyncio
from functions.default import *
from common.mqtt import *

lights_state = "n/a"


def mqtt_lights_loop():
    mqtt_loop("stat/" + mqtt_lights_path + "/#", read_mqtt_lights_state)


def change_lights_state(state):
    mqtt_publish("cmnd/" + mqtt_lights_path + "/POWER1", state)
    return


def read_mqtt_lights_state(client, userdata, message):
    global lights_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/" + mqtt_lights_path + "/POWER1":
        if lights_state != payload_value and not message.retain:
            if payload_value == "ON":
                msg = "Įjungti"
            else:
                msg = "Išjungti"

            asyncio.run(
                send_mqtt_state_to_telegram(f"💡 Šviestuvai {msg}", default_chat_id)
            )

        lights_state = payload_value


def get_lights_state():
    return lights_state

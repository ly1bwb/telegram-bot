import asyncio
from functions.default import *
from common.mqtt import *

monitors_state = "n/a"


def mqtt_monitors_loop():
    mqtt_loop("stat/" + mqtt_monitor_path + "/#", read_mqtt_monitors_state)


def change_monitors_state(state):
    mqtt_publish("cmnd/" + mqtt_monitor_path + "/POWER1", state)
    return


def read_mqtt_monitors_state(client, userdata, message):
    global monitors_state
    payload_value = str(message.payload.decode("utf-8"))
    if message.topic == "stat/" + mqtt_monitor_path + "/POWER":
        if monitors_state != payload_value:
            if payload_value == "ON":
                msg = "Įjungti"
            else:
                msg = "Išjungti"

            # For running on Windows
            # asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

            asyncio.run(
                send_mqtt_state_to_telegram(f"🖥️ Monitoriai {msg}", default_chat_id)
            )

            # alternative method, just for reference
            # loop = asyncio.new_event_loop()
            # loop.run_until_complete(send_mqtt_state_to_telegram(f"🖥️ Monitoriai {msg}", default_chat_id))
            # loop.close()
        monitors_state = payload_value


def get_monitors_state():
    return monitors_state

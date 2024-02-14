from telegram import Update
from telegram.ext import (
    filters,
    CommandHandler,
    MessageHandler,
)
from threading import Thread

from functions.vhf_uhf.radio.vhf_uhf_radio_telegram import *
from functions.vhf_uhf.rotator.vhf_uhf_rotator_telegram import *
from functions.vhf_uhf.switch.vhf.vhf_switch_telegram import *
from functions.vhf_uhf.switch.uhf.uhf_switch_telegram import *
from functions.camera.camera_telegram import *
from functions.lights.lights_telegram import *
from functions.monitors.monitors_telegram import *
from functions.whois.whois_qrz_telegram import *

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("roof_camera", roof_camera))
application.add_handler(CommandHandler("rig_camera", rig_camera))
application.add_handler(CommandHandler("lower_camera", lower_camera))
application.add_handler(CommandHandler("window_camera", window_camera))
application.add_handler(CommandHandler("main_camera", main_camera))
application.add_handler(CommandHandler("vhf_freq", vhf_freq))
application.add_handler(CommandHandler("vhf_azel", vhf_azel))
application.add_handler(CommandHandler("moon", get_moon_vhf_azel))
application.add_handler(CommandHandler("moon_azel", set_moon_vhf_azel))
application.add_handler(CommandHandler("sveiki", sveiki))
application.add_handler(CommandHandler("status", get_status))
application.add_handler(CommandHandler("whois", whois_qrz_query))
application.add_handler(vhf_freq_handler)
application.add_handler(vhf_az_handler)
application.add_handler(vhf_el_handler)
application.add_handler(vhf_mode_handler)
application.add_handler(vhf_sdr_state_handler)
# application.add_handler(uhf_sdr_state_handler)
application.add_handler(monitors_state_handler)
application.add_handler(lights_handler)
application.add_handler(
    MessageHandler(
        filters.Regex(
            r"^\w{2}\d{2}\w{2}(\d\d){0,1}$",
        ),
        calculate_azimuth_by_loc,
    )
)

if __name__ == "__main__":
    mqtt_rig_thread = Thread(target=mqtt_radio_loop)
    mqtt_rig_thread.start()

    mqtt_rot_thread = Thread(target=mqtt_rotator_loop)
    mqtt_rot_thread.start()

    mqtt_vhf_sdr_thread = Thread(target=mqtt_vhf_sdr_loop)
    mqtt_vhf_sdr_thread.start()

    # mqtt_uhf_sdr_thread = Thread(target=mqtt_uhf_sdr_loop)
    # mqtt_uhf_sdr_thread.start()

    mqtt_monitors_thread = Thread(target=mqtt_monitors_loop)
    mqtt_monitors_thread.start()

    mqtt_lights_thread = Thread(target=mqtt_lights_loop)
    mqtt_lights_thread.start()

    # Telegram thread must be last
    telegram_thread = Thread(target=application.run_polling(
        allowed_updates=Update.ALL_TYPES))
    telegram_thread.start()

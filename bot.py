import warnings
warnings.filterwarnings("ignore", message=".*per_message.*")

from telegram import Update, BotCommand
from threading import Thread
from telegram.ext import filters, CommandHandler, MessageHandler
from functions.vhf_uhf.radio.vhf_uhf_radio_telegram import *
from functions.vhf_uhf.rotator.vhf_uhf_rotator_telegram import *
from functions.vhf_uhf.switch.vhf.vhf_switch_telegram import *
from functions.vhf_uhf.switch.uhf.uhf_switch_telegram import *
from functions.hf.rotator.hf_rotator_telegram import *
from functions.camera.camera_telegram import *
from functions.lights.lights_telegram import *
from functions.monitors.monitors_telegram import *
from functions.whois.whois_qrz_telegram import *
from functions.antsw.antsw_telegram import *

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("roof_camera", roof_camera))
application.add_handler(CommandHandler("rig_camera", rig_camera))
application.add_handler(CommandHandler("lower_camera", lower_camera))
application.add_handler(CommandHandler("window_camera", window_camera))
application.add_handler(CommandHandler("main_camera", main_camera))
# application.add_handler(CommandHandler("vhf_freq", vhf_freq))
application.add_handler(CommandHandler("vhf_azel", vhf_azel))
application.add_handler(CommandHandler("hf_az", hf_az))
application.add_handler(CommandHandler("moon", get_moon_vhf_azel))
application.add_handler(CommandHandler("moon_azel", set_moon_vhf_azel))
application.add_handler(CommandHandler("sveiki", sveiki))
application.add_handler(CommandHandler("status", get_status))
application.add_handler(CommandHandler("whois", whois_qrz_query))
application.add_handler(CommandHandler("getant", get_ant))
# application.add_handler(vhf_freq_handler)
application.add_handler(vhf_az_handler)
application.add_handler(vhf_el_handler)
# application.add_handler(vhf_mode_handler)
application.add_handler(vhf_sdr_state_handler)
# application.add_handler(uhf_sdr_state_handler)
application.add_handler(hf_az_handler)
application.add_handler(monitors_state_handler)
application.add_handler(lights_handler)
application.add_handler(antsw_handler)
application.add_handler(geo_az_handler)
application.add_handler(
    MessageHandler(
        filters.Regex(r"^\w{2}\d{2}\w{2}(\d\d){0,1}$"), calculate_azimuth_by_loc
    )
)

# Command menu shown in Telegram clients, published on startup.
bot_commands = [
    BotCommand("lower_camera", "Žemesnė stogo kamera"),
    BotCommand("roof_camera", "Aukštesnė stogo kamera"),
    BotCommand("main_camera", "Patalpos kamera"),
    BotCommand("window_camera", "Vaizdas pro langą"),
    BotCommand("rig_camera", "VHF kamera"),
    # BotCommand("vhf_freq", "VHF stoties dažnis"),
    BotCommand("vhf_azel", "VHF antenų kryptis"),
    BotCommand("hf_az", "HF antenų kryptis"),
    BotCommand("moon", "Mėnulio azimutas ir elevacija"),
    # BotCommand("set_vhf_freq", "Nustatyti VHF dažnį (nariams)"),
    # BotCommand("set_vhf_mode", "Nustatyti VHF režimą (nariams)"),
    BotCommand("set_vhf_az", "Nustatyti VHF azimutą (nariams)"),
    BotCommand("set_vhf_el", "Nustatyti VHF elevaciją (nariams)"),
    BotCommand("set_hf_az", "Nustatyti HF azimutą (nariams)"),
    BotCommand("getant", "Pasirinkta HF antena (nariams)"),
    BotCommand("setant", "Perjungti HF anteną (nariams)"),
    BotCommand("moon_azel", "Nukreipti VHF antenas į Mėnulį (nariams)"),
    BotCommand("vhf_sdr", "VHF SDR switch (nariams)"),
    BotCommand("monitors", "Monitorių valdymas (nariams)"),
    BotCommand("lights", "Šviesų valdymas (nariams)"),
    BotCommand("whois", "Šaukinio informacija (nariams)"),
    BotCommand("status", "Boto versija (nariams)"),
    BotCommand("sveiki", "Sveiki"),
]


async def publish_bot_commands(application):
    await application.bot.set_my_commands(bot_commands)
    log.info(f"Published {len(bot_commands)} commands to the Telegram menu")


application.post_init = publish_bot_commands

if __name__ == "__main__":
    # mqtt_rig_thread = Thread(target=mqtt_vhf_radio_loop, daemon=True)
    # mqtt_rig_thread.start()

    mqtt_vhf_rot_thread = Thread(target=mqtt_vhf_rotator_loop, daemon=True)
    mqtt_vhf_rot_thread.start()

    mqtt_hf_rot_thread = Thread(target=mqtt_hf_rotator_loop, daemon=True)
    mqtt_hf_rot_thread.start()

    mqtt_vhf_sdr_thread = Thread(target=mqtt_vhf_sdr_loop, daemon=True)
    mqtt_vhf_sdr_thread.start()

    # mqtt_uhf_sdr_thread = Thread(target=mqtt_uhf_sdr_loop, daemon=True)
    # mqtt_uhf_sdr_thread.start()

    mqtt_monitors_thread = Thread(target=mqtt_monitors_loop, daemon=True)
    mqtt_monitors_thread.start()

    mqtt_lights_thread = Thread(target=mqtt_lights_loop, daemon=True)
    mqtt_lights_thread.start()

    mqtt_antsw_thread = Thread(target=mqtt_antsw_loop, daemon=True)
    mqtt_antsw_thread.start()

    # Telegram thread must be last
    application.run_polling(allowed_updates=Update.ALL_TYPES)

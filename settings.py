VERSION = "1.9.2"

start_text = "Labas - aš esu LY1BWB stoties botas."

roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"

lower_camera_url = "http://192.168.42.10/webcam/webcam3.jpg"
rig_camera_url = "http://192.168.42.10:8080/?action=snapshot"
window_camera_url = "http://192.168.42.129/snapshot.jpg?"
main_camera_url = (
    "http://192.168.42.183/onvifsnapshot/media_service/snapshot?channel=1&subtype=0"
)

home_qth = "KO24PR15"

valid_users = {
    "LY2EN",
    "sutemos",
    "LY1LB",
    "LY0NAS",
    "LY5AT",
    "LY1WS",
    "LY2DC",
    "LY1JA",
    "keturiantanasursule",
    "volwerene",
    "patriotmef",
    "LY7GG",
    "ly8ja"
}

mqtt_host = "mqtt.vurk"

mqtt_vhf_rot_path = "VURK/rotator/vhf"
mqtt_hf_rot_path = "VURK/rotator/hf"
mqtt_vhf_radio_path = "VURK/radio/IC9700"
mqtt_vhf_sdr_path = "tasmota_E65E89"
mqtt_uhf_sdr_path = "DUMMY"
mqtt_monitor_path = "tasmota_050E88"
mqtt_lights_path = "tasmota_C7DD34"
mqtt_antsw_path = "antsw"

# Antenna switch positions. Keys must match the antenna numbers on the
# AntSwitch device, names are shown in the Telegram menu.
antsw_antennas = {
    "1": "20/15/10m Yagi",
    "2": "40/80m Dipole",
    "3": "Antena 3",
    "4": "Antena 4",
}

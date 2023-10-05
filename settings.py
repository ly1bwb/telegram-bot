VERSION = "1.4.1"

start_text = "Labas - aš esu LY1BWB stoties botas."

roof_camera_host = "http://192.168.42.177/cgi-bin/hi3510/"
roof_camera_url = roof_camera_host + "snap.cgi?&-getpic"

lower_camera_url = "http://192.168.42.10/webcam/webcam3.jpg"
rig_camera_url = "http://192.168.42.10/webcam/webcam1.jpg"
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
    "LY4AU",
    "volwerene"
}

mqtt_host = "mqtt.vurk"

mqtt_vhf_rot_path = "VURK/rotator/vhf"
mqtt_radio_path = "VURK/radio/IC9700"
mqtt_vhf_sdr_path = "tasmota_E65E89"
mqtt_uhf_sdr_path = "DUMMY"
mqtt_monitor_path = "tasmota_050E88"
mqtt_lights_path = "tasmota_C7DD34"

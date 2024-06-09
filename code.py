import time
from display_mode import DisplayMode
import os
import rtc
from device_utils import set_up_esp, set_up_led, set_backlight, connect_to_wifi
from display_utils import play_tap_sound, load_symbols_main, load_symbols_decimal, load_symbols
from dexcom_glucose import DexcomGlucose
from mqtt_utils import create_mqtt_client
import glucose_value_holder

set_up_led()
width, height, py_portal, display, esp32_radio, ts = set_up_esp()

print("Starting up...")

# Board settings
display_turned_off = False

print("Loading fonts...")
font_main = load_symbols_main()
font_decimal = load_symbols_decimal()
font_other = load_symbols()

display_class = DisplayMode(display, width, height, font_main, font_decimal, font_other, False)
display_class.change("LOADING")

# Connect to WiFi
connect_to_wifi(esp32_radio)

# Change to connecting to MQTT
display_class.display_loading_mqtt(py_portal)

mqtt_client = create_mqtt_client(esp32_radio)
mqtt_topic = os.getenv("MQTT_TOPIC")

# Init holder for glucose value
glucose_value_holder.init()
glucose_value_holder.glucose_value = DexcomGlucose(display_class, None, None)

print("Attempting to connect to MQTT")
mqtt_client.connect()

display_class.change("GLUCOSE")

print("Subscribing to %s" % mqtt_topic)
mqtt_client.subscribe(mqtt_topic)

last_touch = time.monotonic()

while True:

    touch = ts.touch_point
    print(touch)

    if touch and time.monotonic() - last_touch >= 1.5:
        last_touch = time.monotonic()
        if display_class.mode == "GLUCOSE" and touch[0] > 260 and 0 < touch[1] < 60:
            # Disconnect and turn display OFF
            play_tap_sound(py_portal)
            display_class.change("OFF")
            display_turned_off = True
            set_backlight(0.0, display)
            mqtt_client.unsubscribe(mqtt_topic)
            time.sleep(1)
            mqtt_client.disconnect()
            time.sleep(1)
            esp32_radio.reset()
        elif display_class.mode == "OFF":
            play_tap_sound(py_portal)
            display_class.change("LOADING")
            display_class.display_loading_wifi()
            display_turned_off = False
            set_backlight(0.75, display)
            # Reconnect to WiFi and MQTT
            esp32_radio.reset()
            time.sleep(1)
            connect_to_wifi(esp32_radio)
            display_class.display_loading_mqtt(py_portal)
            mqtt_client.reconnect()
            time.sleep(1)
            mqtt_client.subscribe(mqtt_topic)
            glucose_value_holder.glucose_value = DexcomGlucose(display_class, None, None)

    if display_turned_off is False:
        try:
            mqtt_client.loop(2)
        except (ValueError, RuntimeError) as e:
            print("Failed to get data, retrying\n", e)
            esp32_radio.reset()
            time.sleep(1)
            connect_to_wifi(esp32_radio)
            mqtt_client.reconnect()
            continue
    else:
        time.sleep(1)

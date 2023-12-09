import time
import adafruit_requests as requests
from display_mode import DisplayMode
import rtc
from adafruit_datetime import datetime, timedelta
from time_utils import get_time, get_timezone_offset
from device_utils import set_up_esp, set_up_led, set_backlight, connect_to_wifi, init_requests
from display_utils import load_symbols, play_tap_sound
from glucose_utils import trigger_glucose_update
from dexcom_session import DexcomSession
from dexcom_glucose import DexcomGlucose

set_up_led()
width, height, py_portal, display, esp32, ts = set_up_esp()

print("Starting up...")

# Board settings
display_turned_off = False

font = load_symbols()

display_mode = DisplayMode(display, width, height, font, False)
display_mode.change("LOADING")

# Get Wi-Fi details and more from a secrets.py file
secrets = connect_to_wifi(esp32)

# Initialize a requests object with a socket and esp32spi interface
init_requests(esp32)

display_mode.display_loading_time()
time.sleep(6)

# get_time will raise OSError if the time isn't available yet so loop until it works.
get_time(esp32, time, rtc)
last_time_fetch = time.monotonic()
offset = get_timezone_offset(requests, time, timedelta)

# Initialize Dexcom connection and retrieves glucose value
display_mode.display_loading_dexcom(py_portal)
num_of_retries: int = 0
dexcom_session = DexcomSession(secrets["dexcom_username"], secrets["dexcom_password"])

dexcom_glucose = DexcomGlucose(None, "NotComputable", datetime.now(), datetime.now() - timedelta(minutes=15))
dexcom_glucose, num_of_retries, next_check = trigger_glucose_update(dexcom_glucose, dexcom_session, display_mode, num_of_retries)
display_mode.change("GLUCOSE")

display_mode.use_us = dexcom_session.us

last_touch = time.monotonic()

print("Starting the program.")
print("-" * 40)

while True:
    touch = ts.touch_point

    if touch and time.monotonic() - last_touch >= 1.5:
        last_touch = time.monotonic()
        if display_mode.mode == "GLUCOSE" and touch[0] > 260 and 0 < touch[1] < 60:
            # sleep
            play_tap_sound(py_portal)
            display_mode.change("OFF")
            display_turned_off = True
            set_backlight(0.0, display)
        elif display_mode.mode == "OFF":
            play_tap_sound(py_portal)
            display_mode.change("GLUCOSE")
            display_turned_off = False
            set_backlight(0.75, display)
    # Prevent to frequent update calls
    # Disable update when screen is off
    if time.monotonic() - next_check >= 0.0 and display_turned_off is False:
        print("Starting to refetch glucose from API.")

        if dexcom_session.is_session_valid() is True:
            dexcom_glucose, num_of_retries, next_check = trigger_glucose_update(dexcom_glucose, dexcom_session,
                                                                                display_mode, num_of_retries)
        else:
            dexcom_session.initialize()
            dexcom_glucose, num_of_retries, next_check = trigger_glucose_update(dexcom_glucose, dexcom_session,
                                                                                display_mode, num_of_retries)

    # Update internal clock, if screen is not turned off
    if display_turned_off is False and time.monotonic() - last_time_fetch >= 1800:
        print("Performing clock update.")
        get_time(esp32, time, rtc)
        last_time_fetch = time.monotonic()

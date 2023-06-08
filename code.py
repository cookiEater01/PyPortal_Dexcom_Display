import time
import board
import neopixel
from digitalio import DigitalInOut
import busio
import adafruit_esp32spi.adafruit_esp32spi_socket as socket
from adafruit_esp32spi import adafruit_esp32spi

import adafruit_requests as requests

# Screen
import adafruit_touchscreen
import displayio
from adafruit_pyportal import PyPortal
from display_utils import black_background, text_box, load_sprite_sheet, prepare_label, prepare_group, play_tap_sound
# from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from sprites import Sprites
import terminalio
from display_mode import DisplayMode

# Dexcom
from dexcom import Dexcom  # , GlucoseValue

# Time
import rtc
from adafruit_datetime import datetime, timedelta
from time_utils import get_time, get_timezone_offset
from utils import set_backlight

# Sensors
# from analogio import AnalogIn


print("Starting up...")

# Board settings
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
# light_sensor is uselles because it is located above the usb port and is
# hidden behind the plastic housing.
# light_sensor = AnalogIn(board.LIGHT)
display_turned_off = False


# ESP32
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Display
display = board.DISPLAY

# Default brightness is 0.99
set_backlight(0.75, display)

WIDTH = board.DISPLAY.width
HEIGHT = board.DISPLAY.height

ts = adafruit_touchscreen.Touchscreen(
    board.TOUCH_XL,
    board.TOUCH_XR,
    board.TOUCH_YD,
    board.TOUCH_YU,
    calibration=((5200, 59000), (5800, 57000)),
    size=(WIDTH, HEIGHT),
)
pyportal = PyPortal(esp=esp, external_spi=spi)

# Set the font and preload letters
font_glucose = bitmap_font.load_font("/fonts/OpenSans-Regular-50.bdf")
font_glucose.load_glyphs(b"lmoLM1234567890- ().")

# Main (Screen) DisplayIO Group
screen_group = displayio.Group()
display.show(screen_group)

# Add background to main screen
screen_group.append(black_background(displayio, WIDTH, HEIGHT))

# Define two views
loading_view = displayio.Group()
glucose_view = displayio.Group()
settings_view = displayio.Group()

screen_group.append(loading_view)

# Group for loading image(s)
loading_image_group = prepare_group(110, 40)

# Loading images sprites
loading_tg = load_sprite_sheet("/images/loading_sprites.bmp", 100, 100)
loading_sprites = Sprites(loading_tg, 3, loading_image_group)
loading_sprites.add_to_group()

# Add loading image group to  loading view
loading_view.append(loading_image_group)

# Group and loading label
loading_label_group = displayio.Group()
loading_status_label = prepare_label(terminalio.FONT, "Connecting to WIFI ...", 0xFFFFFF, (0.5, 0.5), (WIDTH / 2, HEIGHT * 3 / 4), loading_label_group)

# Append loading_label_group to loading view
loading_view.append(loading_label_group)


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

time.sleep(6)
# requests.set_socket(socket, esp)


print("Connecting to WiFi %s..." % secrets["ssid"])
while not esp.is_connected:
    try:
        esp.connect(secrets)
    except OSError as e:
        print("Could not connect to WiFI, retrying: ", e)
        continue
print("Connected to", str(esp.ssid, "utf-8"), "\tRSSI:", esp.rssi)
print("My IP address is", esp.pretty_ip(esp.ip_address))

# Show second sprite and update loading text
loading_sprites.update_tile(1)
loading_status_label.text = "Acquiring time ..."

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

time.sleep(6)

# get_time will raise OSError if the time isn't available yet so loop until it works.
get_time(esp, time, rtc)
last_time_fetch = time.monotonic()
offset = get_timezone_offset(requests, time, timedelta)


# Show last sprite in loading sequence and update and break text
loading_sprites.update_tile(2)
text_box(
    loading_status_label,
    HEIGHT * 3 / 4,
    20,
    "Initializing Dexcom connection ...",
    pyportal,
    terminalio.FONT,
)

# Initialize Dexcom connection and retrieves glucose value
dexcom_object = Dexcom(secrets["dexcom_username"], secrets["dexcom_password"], requests)
glucose_value = dexcom_object.get_latest_glucose_value(requests)


timer = time.monotonic()
last_touch = time.monotonic()

print("Starting the program.")
print("-" * 40)

# Prepare glucose view

# Group for glucose unit
settings_icon_group = prepare_group(270, 0)

settings_icon_tg = load_sprite_sheet("/images/gear.bmp", 50, 50)
settings_sprites = Sprites(settings_icon_tg, 1, settings_icon_group)
settings_sprites.add_to_group()

# Add glucose unit group to view
glucose_view.append(settings_icon_group)

# Glucose image(s) group
glucose_image_group = prepare_group(55+17, 10)

# Add glucose image group to view
glucose_view.append(glucose_image_group)

# Glucose images sprites
glucose_tg = load_sprite_sheet("/images/glucose_sprites.bmp", 200, 222)
glucose_sprites = Sprites(glucose_tg, 24, glucose_image_group)
glucose_sprites.add_to_group()

# Group for glucose value
glucose_value_group = displayio.Group()

glucose_label = prepare_label(font_glucose, "", 0x000000, (0.5, 0.5), (156, 121), glucose_value_group)

# Add glucose value group to view
glucose_view.append(glucose_value_group)

# Group for glucose unit
glucose_unit_group = displayio.Group()

glucose_unit_label = prepare_label(terminalio.FONT, "mmol/L" if dexcom_object.use_mmol is True else "mg/dl", 0x000000, (0.5, 0.5), (156, 165), glucose_unit_group)

# Add glucose unit group to view
glucose_view.append(glucose_unit_group)

# Group for last glucose update
glucose_update_group = displayio.Group()

glucose_update_label = prepare_label(terminalio.FONT, "", 0xFFFFFF, (0.5, 0.5), (156, 230), glucose_update_group)

# Add glucose unit group to view
glucose_view.append(glucose_update_group)

# Show correct values on screen
glucose_value.update_view(
    glucose_sprites, glucose_label, glucose_unit_label, glucose_update_label, offset, dexcom_object.use_mmol
)

# Switch views
screen_group.remove(loading_view)
screen_group.append(glucose_view)

display_mode = DisplayMode()

# Back button group
back_button_group = prepare_group(0, 0)
sleep_button_group = prepare_group(50, 80)
unit_button_group = prepare_group(190, 80)

# Add back image group to view
settings_view.append(back_button_group)

# Back image sprite
back_tg = load_sprite_sheet("/images/previous.bmp", 50, 50)
back_sprites = Sprites(back_tg, 1, back_button_group)
back_sprites.add_to_group()

# Add sleep image group to view
settings_view.append(sleep_button_group)

# Sleep image sprite
sleep_tg = load_sprite_sheet("/images/sleep.bmp", 80, 80)
sleep_sprites = Sprites(sleep_tg, 1, sleep_button_group)
sleep_sprites.add_to_group()

sleep_label_bottom_group = displayio.Group()
sleep_label_bottom_label = prepare_label(terminalio.FONT, "Turn off", 0xFFFFFF, (0.5, 0.5), (90, 170), sleep_label_bottom_group)
settings_view.append(sleep_label_bottom_group)

# Add unit image group to view
settings_view.append(unit_button_group)

# Unit image sprite
unit_tg = load_sprite_sheet("/images/unit.bmp", 80, 80)
unit_sprites = Sprites(unit_tg, 1, unit_button_group)
unit_sprites.add_to_group()

# Unit label
unit_label_top_group = displayio.Group()
unit_label_top_label = prepare_label(terminalio.FONT, "mmol/L", 0xFFFFFF, (0.5, 0.5), (230, 70), unit_label_top_group)
settings_view.append(unit_label_top_group)

unit_label_bottom_group = displayio.Group()
unit_label_bottom_label = prepare_label(terminalio.FONT, "mg/dL", 0xFFFFFF, (0.5, 0.5), (230, 170), unit_label_bottom_group)
settings_view.append(unit_label_bottom_group)

while True:
    touch = ts.touch_point

    if touch and time.monotonic() - last_touch >= 1.0:
        last_touch = time.monotonic()
        if display_mode.mode == "GLUCOSE" and touch[0] > 260 and touch[1] > 0 and touch[1] < 60:
            # switch to settings screen
            display_mode.change("SETTINGS")
            play_tap_sound(pyportal)
            screen_group.remove(glucose_view)
            screen_group.append(settings_view)
        elif display_mode.mode == "SETTINGS":
            # switch to settings screen
            if touch[0] < 60 and touch[1] < 60:
                # back clicked
                display_mode.change("GLUCOSE")
                play_tap_sound(pyportal)
                screen_group.remove(settings_view)
                screen_group.append(glucose_view)
            elif touch[0] >= 40 and touch[0] <= 130 and touch[1] >= 70 and touch[1] <= 170:
                # sleep
                display_mode.change("OFF")
                play_tap_sound(pyportal)
                screen_group.remove(settings_view)
                screen_group.append(glucose_view)
                display_turned_off = True
                set_backlight(0.0, display)
            elif touch[0] >= 180 and touch[0] <= 280 and touch[1] >= 70 and touch[1] <= 170:
                # unit
                play_tap_sound(pyportal)
                dexcom_object.use_mmol = not dexcom_object.use_mmol
                glucose_value.update_unit(glucose_label, glucose_unit_label, dexcom_object.use_mmol)
                display_mode.change("GLUCOSE")
                screen_group.remove(settings_view)
                screen_group.append(glucose_view)
        elif display_mode.mode == "OFF":
            play_tap_sound(pyportal)
            display_mode.change("GLUCOSE")
            display_turned_off = False
            set_backlight(0.75, display)
    # Prevent to frequent update calls, wait for 30s between API calls
    # Disable update when screen is off
    if time.monotonic() - timer >= 30.0 and board.DISPLAY.brightness > 0.0:
        print("Performing glucose value update.")
        if datetime.now() >= dexcom_object.next_update:
            glucose_value = dexcom_object.get_latest_glucose_value(requests)
            glucose_value.update_view(
                glucose_sprites, glucose_label, glucose_unit_label, glucose_update_label, offset, dexcom_object.use_mmol
            )
        timer = time.monotonic()

    # Update internal clock, if screen is not turned off
    if board.DISPLAY.brightness > 0.0 and time.monotonic() - last_time_fetch >= 1800:
        print("Performing clock update.")
        get_time(esp, time, rtc)
        last_time_fetch = time.monotonic()

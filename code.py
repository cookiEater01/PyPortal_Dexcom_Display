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
from display_utils import black_background, text_box, load_sprite_sheet
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from sprites import Sprites
import terminalio

# Dexcom
from dexcom import Dexcom, GlucoseValue

# Time
import rtc
from adafruit_datetime import datetime, timedelta

# Sensors
from analogio import AnalogIn

from random import randrange


print("Starting up...")

# Sound Effects
soundDemo = "/sounds/sound.wav"
soundBeep = "/sounds/beep.wav"
soundTab = "/sounds/tab.wav"

# Board settings
pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
light_sensor = AnalogIn(board.LIGHT)

# ESP32
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)

spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# Display
display = board.DISPLAY

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

screen_group.append(loading_view)

# Group for loading image(s)
loading_image_group = displayio.Group()
loading_image_group.x = 110
loading_image_group.y = 40

# Loading images sprites
loading_tg = load_sprite_sheet("/images/loading_sprites.bmp", 100, 100)
loading_sprites = Sprites(loading_tg, 3, loading_image_group)
loading_sprites.add_to_group()

# Add loading image group to  loading view
loading_view.append(loading_image_group)

# Group for loading label
loading_label_group = displayio.Group()

loading_status_label = Label(terminalio.FONT)
loading_status_label.text = "Connecting to WIFI ..."
loading_status_label.anchor_point = (0.5, 0.5)
loading_status_label.anchored_position = (WIDTH / 2, HEIGHT * 3 / 4)
loading_label_group.append(loading_status_label)

# Append loading_label_group to loading view
loading_view.append(loading_label_group)

# Backlight function
# Value between 0 and 1 where 0 is OFF, 0.5 is 50% and 1 is 100% brightness.
def set_backlight(val: float):
    val = max(0, min(1.0, val))
    board.DISPLAY.auto_brightness = False
    board.DISPLAY.brightness = val


# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

requests.set_socket(socket, esp)


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

# get_time will raise OSError if the time isn't available yet so loop until it works.
now_utc = None
print("Waiting for ESP to aquire localtime.", end=" ")
while now_utc is None:
    try:
        esp_time = esp.get_time()
        now_utc = time.localtime(esp_time[0])
        print("Time aquired.")
    except OSError:
        pass
rtc.RTC().datetime = now_utc

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

# Glucose image(s) group
glucose_image_group = displayio.Group()
glucose_image_group.x = 55 + 17
glucose_image_group.y = 10

# Add glucose image group to view
glucose_view.append(glucose_image_group)

# Glucose images sprites
glucose_tg = load_sprite_sheet("/images/glucose_sprites.bmp", 200, 222)
glucose_sprites = Sprites(glucose_tg, 24, glucose_image_group)
glucose_sprites.add_to_group()

# Group for glucose value
glucose_value_group = displayio.Group()

glucose_label = Label(font_glucose)
glucose_label.text = ""
glucose_label.color = 0x000000
glucose_label.anchor_point = (0.5, 0.5)
glucose_label.anchored_position = (156, 121)

# Add glucose value label to group
glucose_value_group.append(glucose_label)

# Add glucose value group to view
glucose_view.append(glucose_value_group)

# Group for glucose unit
glucose_unit_group = displayio.Group()

glucose_unit_label = Label(terminalio.FONT)
glucose_unit_label.text = "mmol/L"
glucose_unit_label.color = 0x000000
glucose_unit_label.anchor_point = (0.5, 0.5)
glucose_unit_label.anchored_position = (156, 165)

# Add glucose unit label to group
glucose_unit_group.append(glucose_unit_label)

# Add glucose unit group to view
glucose_view.append(glucose_unit_group)

# Group for last glucose update
glucose_update_group = displayio.Group()

glucose_update_label = Label(terminalio.FONT)
glucose_update_label.text = ""
glucose_update_label.color = 0xFFFFFF
glucose_update_label.anchor_point = (0.5, 0.5)
glucose_update_label.anchored_position = (156, 230)

# Add glucose unit label to group
glucose_update_group.append(glucose_update_label)

# Add glucose unit group to view
glucose_view.append(glucose_update_group)

# Show correct values on screen
glucose_value.update_view(
    glucose_sprites, glucose_label, glucose_unit_label, glucose_update_label
)

# Switch views
screen_group.remove(loading_view)
screen_group.append(glucose_view)

while True:
    p = ts.touch_point
    if p and time.monotonic() - last_touch >= 1.0:
        pyportal.play_file(soundBeep)
        print("Touch detected.")
        last_touch = time.monotonic()
        if board.DISPLAY.brightness != 0.0:
            set_backlight(0.0)
        else:
            set_backlight(0.9)
    # Prevent to frequent update calls, wait for 10s between API calls
    # Disable update when screen is off
    if time.monotonic() - timer >= 30.0 and board.DISPLAY.brightness > 0.0:
        timer = time.monotonic()
        if datetime.now() >= glucose_value.next_fetch:
            glucose_value = dexcom_object.get_latest_glucose_value(requests)
            glucose_value.update_view(
                glucose_sprites, glucose_label, glucose_unit_label, glucose_update_label
            )

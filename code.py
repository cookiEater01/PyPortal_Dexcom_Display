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
from display_utils import black_background, text_box, set_image
from adafruit_display_text.label import Label
from adafruit_bitmap_font import bitmap_font
from adafruit_button import Button
from adafruit_display_shapes.circle import Circle

# Dexcom
from dexcom import Dexcom, GlucoseValue

# Time
import rtc
from adafruit_datetime import datetime, timedelta

#Sensors
from analogio import AnalogIn


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
font = bitmap_font.load_font("/fonts/VCROSDMono-17a.bdf")
font.load_glyphs(b'abcdefghjiklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890- ()')

font_glucose = bitmap_font.load_font("/fonts/OpenSans-Regular-50.bdf")
font_glucose.load_glyphs(b'lmoLM1234567890- ().')

# Root DisplayIO
root_group = displayio.Group()
display.show(root_group)

# Create a new DisplayIO group
splash = displayio.Group()
splash.append(black_background(displayio, WIDTH, HEIGHT))

loading_view = displayio.Group()
glucose_view = displayio.Group()

splash.append(loading_view)

image_group = displayio.Group()
image_group.x = 110
image_group.y = 40
loading_view.append(image_group)
set_image(image_group, "/images/wifi.bmp", displayio)

label_group = displayio.Group()

status_label = Label(font)
status_label.text = "Connecting to WIFI ..."
status_label.anchor_point = (0.5, 0.5)
status_label.anchored_position = (WIDTH / 2, HEIGHT * 3 / 4)
label_group.append(status_label)

# append label_group to splash
loading_view.append(label_group)

# Show the group
display.show(splash)

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

set_image(image_group, "/images/clock.bmp", displayio)

status_label.text = "Acquiring time ..."

# Initialize a requests object with a socket and esp32spi interface
socket.set_interface(esp)
requests.set_socket(socket, esp)

# get_time will raise OSError if the time isn't available yet so loop until it works.
now_utc = None
print("Waiting for ESP to aquire localtime.", end = " ")
while now_utc is None:
    try:
        esp_time = esp.get_time()
        now_utc = time.localtime(esp_time[0])
        print("Time aquired.")
    except OSError:
        pass
rtc.RTC().datetime = now_utc

set_image(image_group, "/images/dexcom.bmp", displayio)

text_box(status_label, HEIGHT * 3 / 4, 20, "Initializing Dexcom connection ...", pyportal, font)

# Initialize Dexcom connection and retrieves glucose value
# dexcom_object = Dexcom(secrets["dexcom_username"], secrets["dexcom_password"], requests)
# glucose_value = dexcom_object.get_latest_glucose_value(requests)

timer = time.monotonic()
last_touch = time.monotonic()

print("Starting the program.")
print("-" * 40)

#Prepare glucose view display

circle_main = Circle(160, 120, 90, fill=0xc6c6c6, outline=0xffffff, stroke=2)
circle_out = Circle(160, 120, 100, fill=None, outline=0xa9a9a9, stroke=12)
glucose_view.append(circle_main)
glucose_view.append(circle_out)

glucose_group = displayio.Group()

glucose_label = Label(font_glucose)
glucose_label.text = "8.4"
glucose_label.anchor_point = (0.5, 0.5)
glucose_label.anchored_position = (180, 120)
# glucose_group.append(glucose_label)

glucose_view.append(glucose_label)

splash.remove(loading_view)
splash.append(glucose_view)

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
    if time.monotonic() - timer >= 10.0:
        timer = time.monotonic()
        # if datetime.now() >= glucose_value.next_fetch:
        #    glucose_value = dexcom_object.get_latest_glucose_value(requests)


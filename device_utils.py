import board
from digitalio import DigitalInOut
import busio
import os
from adafruit_esp32spi import adafruit_esp32spi
import adafruit_touchscreen
from adafruit_pyportal import PyPortal
import neopixel
import time
import adafruit_connection_manager
import adafruit_requests


def set_up_led():
    print("Setting LED...")
    pixel = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=0)
    # light_sensor is useless because it is located above the usb port, and it is
    # hidden behind the plastic housing.
    # light_sensor = AnalogIn(board.LIGHT)
    return pixel


def set_up_esp():
    print("Setting ESP...")

    # ESP32
    esp32_cs = DigitalInOut(board.ESP_CS)
    esp32_ready = DigitalInOut(board.ESP_BUSY)
    esp32_reset = DigitalInOut(board.ESP_RESET)

    spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
    esp_radio = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

    # Display
    display = board.DISPLAY

    # Default brightness is 0.99
    set_backlight(0.75, display)

    width = board.DISPLAY.width
    height = board.DISPLAY.height

    ts = adafruit_touchscreen.Touchscreen(
        board.TOUCH_XL,
        board.TOUCH_XR,
        board.TOUCH_YD,
        board.TOUCH_YU,
        calibration=((5200, 59000), (5800, 57000)),
        size=(width, height),
    )
    py_portal = PyPortal(esp=esp_radio, external_spi=spi)
    return width, height, py_portal, display, esp_radio, ts


# Backlight function
# Value between 0 and 1 where 0 is OFF, 0.5 is 50% and 1 is 100% brightness.
def set_backlight(val: float, display):
    val = max(0, min(1.0, val))
    print("Setting backlight to " + str(val))
    display.brightness = val


def connect_to_wifi(esp32_radio):
    # Get Wi-Fi details and more from a secrets.py file
    wifi_ssid = os.getenv("WIFI_SSID")
    wifi_password = os.getenv("WIFI_PASSWORD")

    time.sleep(6)
    print("Connecting to WiFi %s..." % wifi_ssid)
    while not esp32_radio.is_connected:
        try:
            esp32_radio.connect_AP(wifi_ssid, wifi_password)
        except OSError as e:
            print("Could not connect to WiFI, retrying: ", e)
            continue
    print("Connected to", str(esp32_radio.ssid, "utf-8"), "\tRSSI:", esp32_radio.rssi)
    print("My IP address is", esp32_radio.pretty_ip(esp32_radio.ip_address))
    return

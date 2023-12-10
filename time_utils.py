from const import TIMEZONE, WORLD_TIME_API_ENDPOINT
from adafruit_requests import OutOfRetries


def get_time(esp, time, rtc):
    now_utc = None
    print("Waiting for ESP to acquire localtime.", end=" ")
    while now_utc is None:
        try:
            esp_time = esp.get_time()
            now_utc = time.localtime(esp_time[0])
            print("Time aquired.")
        except OSError:
            pass
    rtc.RTC().datetime = now_utc


def get_timezone_offset(requests, time, timedelta):
    print("Getting timezone offset from UTC.")
    response = None
    retries = 0

    while response is None and retries < 10:
        try:
            response = requests.get(WORLD_TIME_API_ENDPOINT + TIMEZONE)
            response_json = response.json()
            response.close()

            offset_str = response_json["utc_offset"]
            return convert_offset(offset_str, timedelta)
        except (ValueError, RuntimeError, OSError, OutOfRetries) as e:
            print("An error occurred:", e)
            retries += 1
            time.sleep(1)


def convert_offset(utc_offset, timedelta):
    print("Converting timezone offset to seconds.")

    # Extract the sign, hour, and minute values from the UTC offset
    sign = utc_offset[0]
    hours, minutes = map(int, utc_offset[1:].split(":"))

    # Determine the sign multiplier
    sign_multiplier = 1 if sign == "+" else -1

    # Extract the hour and minute values from the UTC offset
    hours, minutes = map(int, utc_offset.split(":"))

    # Parse the offset string into a timedelta object
    offset_seconds = timedelta(hours=sign_multiplier * hours, minutes=sign_multiplier * minutes).total_seconds()

    # Convert the timedelta object to seconds
    return offset_seconds

import time

from dexcom_glucose import DexcomGlucose
import json
from adafruit_datetime import datetime, timedelta
from dexcom_session import DexcomSession
import adafruit_requests as requests
from utils import parse_date
from display_mode import DisplayMode

from const import (
    DEXCOM_GLUCOSE_READINGS_ENDPOINT
)


def trigger_glucose_update(old_glucose: DexcomGlucose, dexcom_session: DexcomSession, display: DisplayMode, num_of_retries: int, offset: int):
    print("-" * 40)
    print("Triggering glucose update.")
    display.add_refreshing()
    old_time = old_glucose.utc_time
    new_glucose = get_latest_glucose_value(dexcom_session, offset)
    dexcom_session.last_time_used = datetime.now()
    sleep_for: int

    time_diff = old_time - new_glucose.utc_time

    if new_glucose.mgdl is None or time_diff.total_seconds() == 0:
        num_of_retries = num_of_retries + 1
        print("Glucose value invalid for " + str(num_of_retries) + " times in the row.")
        if num_of_retries == 1:
            sleep_for = 30
        elif num_of_retries == 2:
            sleep_for = 30
        elif num_of_retries == 3:
            display.add_warning()
            sleep_for = 60
        elif num_of_retries == 4:
            sleep_for = 120
        else:
            new_glucose.mgdl = None
            new_glucose.mmol = None
            display.update_glucose(new_glucose)
            sleep_for = 150
    else:
        print("Successfully received new glucose.")
        num_of_retries = 0
        display.remove_warning()
        display.update_glucose(new_glucose)

        next_glucose = new_glucose.utc_time + timedelta(minutes=5) + timedelta(seconds=25)
        now = datetime.now()

        diff = next_glucose - now
        sleep_for = max(1, diff.total_seconds())
    display.remove_refreshing()
    print("Sleep for " + str(sleep_for) + "s.")
    return new_glucose, num_of_retries, datetime.now() + timedelta(seconds=sleep_for)


def get_latest_glucose_value(dexcom_session: DexcomSession, offset: int):
    # Get latest glucose value
    print("Getting latest glucose value...")

    body = {
        "sessionId": dexcom_session.session_id,
        "maxCount": 1,
        "minutes": 10,
    }

    header = {"Content-Type": "application/json"}

    print("Posting request for glucose value")

    response = requests.post(
        dexcom_session.base_url + DEXCOM_GLUCOSE_READINGS_ENDPOINT,
        data=json.dumps(body),
        headers=header,
    )

    if response.status_code == 200:
        response_array = response.json()

        print("Number of received glucose values: ", len(response_array))

        response.close()

        if len(response_array) > 0:
            latest = response_array[0]
            return DexcomGlucose(int(latest["Value"]), latest["Trend"], parse_date(latest["DT"]), parse_date(latest["WT"]))
        else:
            return DexcomGlucose(None, "NotComputable", datetime.now() + timedelta(seconds=offset), datetime.now())
    else:
        print("Response status: ", response.status_code)
        return DexcomGlucose(None, "NotComputable", datetime.now() + timedelta(seconds=offset), datetime.now())

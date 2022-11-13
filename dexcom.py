import json
from adafruit_datetime import datetime, timedelta
from utils import mgdl_to_mmol, get_dt_from_epoch

from const import (
    DEXCOM_URL,
    DEXCOM_URL_US,
    DEXCOM_APPLICATION_ID,
    DEXCOM_AUTHENTICATE_ENDPOINT,
    DEXCOM_LOGIN_ID_ENDPOINT,
    DEXCOM_GLUCOSE_READINGS_ENDPOINT,
)


class GlucoseValue:
    # Class for storing latest glucose value, trend and time of measurement

    def __init__(self, mgdl: int, trend: str, time: str):
        self.mgdl = mgdl
        self.mmol = mgdl_to_mmol(mgdl)
        self.trend = trend
        self.time = datetime.fromisoformat(get_dt_from_epoch(time))
        self.next_fetch = self.time + timedelta(minutes=5, seconds=30)
        print(self)

    def __repr__(self):
        return f"<GlucoseValue mgdl:{self.mgdl} mmol:{self.mmol} trend:{self.trend} time:{self.time} next_fetch:{self.next_fetch}>"


class Dexcom:
    # Class for communitaion with Dexcom Share API.

    def __init__(self, username: str, password: str, requests, us: bool = False):
        if us is True:
            self.base_url = DEXCOM_URL_US
        else:
            self.base_url = DEXCOM_URL
        self.username = username
        self.password = password
        self.session_id = None
        self.account_id = None
        self.validate_account()
        self.get_account_id(requests)
        self.get_session_id(requests)

    def validate_account(self):
        # Validate credentials
        if not self.username:
            print("Username cannot be empty.")
            raise
        if not self.password:
            print("Password cannot be empty.")
            raise

    def validate_account_id(self):
        # Validate if account_id is set
        if self.account_id is None:
            print("account_id is None")
            raise

    def validate_session_id(self):
        # Validate if session_id is set
        if self.session_id is None:
            print("session_id is None")
            raise

    def get_account_id(self, requests):
        # Get Account Id
        print("-" * 40)
        print("Getting Dexcom Accound ID...")

        body = {
            "applicationId": DEXCOM_APPLICATION_ID,
            "accountName": self.username,
            "password": self.password,
        }

        header = {"Content-Type": "application/json"}

        print("Posting data for accound id")

        response = requests.post(
            self.base_url + DEXCOM_AUTHENTICATE_ENDPOINT,
            data=json.dumps(body),
            headers=header,
        )

        print("Response: ", response.text.strip('"'))
        print("-" * 40)

        self.account_id = response.text.strip('"')

        response.close()

    def get_session_id(self, requests):
        # Get Session Id
        print("-" * 40)
        print("Getting Dexcom Share Session ID...")

        self.validate_account_id()

        body = {
            "applicationId": DEXCOM_APPLICATION_ID,
            "accountId": self.account_id,
            "password": self.password,
        }

        header = {"Content-Type": "application/json"}

        print("Posting data for session id")

        response = requests.post(
            self.base_url + DEXCOM_LOGIN_ID_ENDPOINT,
            data=json.dumps(body),
            headers=header,
        )

        print("Response: ", response.text.strip('"'))
        print("-" * 40)

        self.session_id = response.text.strip('"')

        response.close()

    def get_latest_glucose_value(self, requests):
        # Get latest glucose value
        print("-" * 40)
        print("Getting latest glucose value...")

        self.validate_session_id()

        body = {
            "sessionId": self.session_id,
            "maxCount": 1,
            "minutes": 10,
        }

        header = {"Content-Type": "application/json"}

        print("Posting request for glucose value")

        response = requests.post(
            self.base_url + DEXCOM_GLUCOSE_READINGS_ENDPOINT,
            data=json.dumps(body),
            headers=header,
        )

        response_array = response.json()

        print("Response lenght: ", len(response_array))
        print("Response: ", response_array)
        print("-" * 40)

        response.close()

        if len(response_array) > 0:
            latest = response_array[0]
            return GlucoseValue(int(latest["Value"]), latest["Trend"], latest["WT"])
        else:
            return None

import json
from adafruit_datetime import datetime, timedelta
from utils import mgdl_to_mmol, get_dt_from_epoch
from sprites import Sprites
from session import Session
from glucose_value import GlucoseValue

from const import (
    DEXCOM_URL,
    DEXCOM_URL_US,
    DEXCOM_APPLICATION_ID,
    DEXCOM_AUTHENTICATE_ENDPOINT,
    DEXCOM_LOGIN_ID_ENDPOINT,
    DEXCOM_GLUCOSE_READINGS_ENDPOINT,
)


class Dexcom:
    # Class for communitaion with Dexcom Share API.

    def __init__(self, username: str, password: str, requests, us: bool = False, use_mmol: bool = True):
        if us is True:
            self.base_url = DEXCOM_URL_US
        else:
            self.base_url = DEXCOM_URL
        self.username = username
        self.password = password
        self.session = None
        self.account_id = None
        self.next_update = None
        self.use_mmol = use_mmol
        self.connect(requests)


    def connect(self, requests):
        self.get_account_id(requests)
        self.get_session_id(requests)


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

        self.session = Session(response.text.strip('"'), datetime.now())

        response.close()

    def get_latest_glucose_value(self, requests):
        # Get latest glucose value
        print("-" * 40)
        print("Getting latest glucose value...")

        if self.session.is_session_valid() is False:
            self.connect(requests)

        body = {
            "sessionId": self.session.session_id,
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
        print("-" * 40)

        response.close()

        self.next_update = datetime.now() + timedelta(minutes=2)
        self.num_of_errors = 0
        self.session.last_used_time = datetime.now()

        if len(response_array) > 0:
            latest = response_array[0]
            return GlucoseValue(int(latest["Value"]), latest["Trend"], get_dt_from_epoch(latest["WT"]))
        else:
            return GlucoseValue(None, "NotComputable", datetime.now().isoformat())

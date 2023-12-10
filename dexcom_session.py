from const import (
    USE_US,
    DEXCOM_URL,
    DEXCOM_URL_US,
    DEXCOM_APPLICATION_ID,
    DEXCOM_AUTHENTICATE_ENDPOINT,
    DEXCOM_LOGIN_ID_ENDPOINT,
)

import json
from adafruit_datetime import datetime, timedelta
import adafruit_requests as requests


class DexcomSession:

    def __init__(self, username: str, password: str):
        print("Creating DexcomSession object")
        if USE_US == "false":
            self.base_url: str = DEXCOM_URL
            self.us = False
        else:
            self.base_url: str = DEXCOM_URL_US
            self.us = True
        self.username: str = username
        self.password: str = password
        self.account_id: str | None = None
        self.session_id: str | None = None
        self.last_time_used: str | None = None
        self.initialize()

    def initialize(self):
        print("Initializing DexcomSession object")
        self.get_account_id()
        self.get_session_id()

    def is_session_valid(self):
        return False if datetime.now() > self.last_time_used + timedelta(hours=1) else True

    def get_account_id(self):
        # Get AccountId
        print("-" * 40)
        print("Getting Dexcom account ID...")

        body = {
            "applicationId": DEXCOM_APPLICATION_ID,
            "accountName": self.username,
            "password": self.password,
        }

        header = {"Content-Type": "application/json"}

        print("Posting data for account id")

        response = requests.post(
            self.base_url + DEXCOM_AUTHENTICATE_ENDPOINT,
            data=json.dumps(body),
            headers=header,
        )

        print("Response: ", response.text.strip('"'))
        print("-" * 40)

        self.account_id = response.text.strip('"')

        response.close()

    def get_session_id(self):
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

        self.session_id = response.text.strip('"')
        self.last_time_used = datetime.now()

        response.close()

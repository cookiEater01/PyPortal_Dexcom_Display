
from const import WORLD_TIME_API_ENDPOINT

class TimeZone:
    def __init__(self, timezone: str, requests, time, timedelta):
        print("Init TimeZone")
        self.offset = None
        self.timezone = timezone
        self.get_offset(requests, time, timedelta)

    def get_offset(self, requests, time, timedelta):
        print("Get offset")
        response = None
        retries = 0

        while response is None and retries < 10:
            try:
                response = requests.get(WORLD_TIME_API_ENDPOINT + self.timezone)
                response_json = response.json()
                response.close()

                offset_str = response_json["utc_offset"]
                self.convert_offset(offset_str, timedelta)
            except (ValueError, RuntimeError) as e:
                print("An error occurred:", e)
                retries += 1
                time.sleep(1)


    def convert_offset(self, utc_offset, timedelta):

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
        self.offset = offset_seconds


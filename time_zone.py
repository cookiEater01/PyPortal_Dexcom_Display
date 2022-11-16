
from const import WORLD_TIME_API_ENDPOINT

class TimeZone:
    def __init__(self, timezone: str, requests):
        self.offset = None
        self.timezone = timezone
        self.get_offset(requests)

    def get_offset(self, requests):

        response = requests.get(WORLD_TIME_API_ENDPOINT + self.timezone)
        response_json = response.json()
        response.close()

        self.offset = int(response_json["raw_offset"])


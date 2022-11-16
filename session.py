from adafruit_datetime import datetime, timedelta

class Session:
    def __init__(self, session_id, last_used_time):
        self.session_id = session_id
        self.last_used_time = last_used_time

    def is_session_valid(self):
        return False if datetime.now() > self.last_used_time + timedelta(hours=1) else True

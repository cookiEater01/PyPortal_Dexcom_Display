from adafruit_datetime import datetime, timedelta
from utils import mgdl_to_mmol, get_dt_from_epoch
from sprites import Sprites
from time_zone import TimeZone

TRENDS = {
    "Flat": 1,
    "FortyFiveUp": 2,
    "SingleUp": 3,
    "DoubleUp": 4,
    "FortyFiveDown": 5,
    "SingleDown": 6,
    "DoubleDown": 7,
}

class GlucoseValue:
    # Class for storing latest glucose value, trend and time of measurement

    def __init__(self, mgdl: int, trend: str, time: str):
        self.mgdl = mgdl
        self.mmol = mgdl_to_mmol(mgdl)
        self.trend = trend
        self.trend_numeric = TRENDS[self.trend]
        self.time = datetime.fromisoformat(get_dt_from_epoch(time))
        print(self)

    def __repr__(self):
        return f"<GlucoseValue mgdl:{self.mgdl} mmol:{self.mmol} trend:{self.trend} time:{self.time}>"

    def update_view(self, sprites, value_label, unit_label, update_label, offset):
        if self.mmol <= 4.0:
            sprites.update_tile(self.trend_numeric + 8)
            value_label.color = 0xFFFFFF
            unit_label.color = 0xFFFFFF
        elif self.mmol >= 8.0:
            sprites.update_tile(self.trend_numeric + 16)
            value_label.color = 0x000000
            unit_label.color = 0x000000
        else:
            sprites.update_tile(self.trend_numeric)
            value_label.color = 0x000000
            unit_label.color = 0x000000
        value_label.text = str(self.mmol)
        tmp_time = self.time + timedelta(seconds=int(offset.offset))
        update_label.text = "{:02d}:{:02d}".format(tmp_time.time().hour, tmp_time.time().minute)

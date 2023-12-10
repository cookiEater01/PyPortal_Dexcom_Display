from adafruit_datetime import datetime
from utils import mgdl_to_mmol

TRENDS = {
    "NotComputable": 0,
    "Flat": 1,
    "FortyFiveUp": 2,
    "SingleUp": 3,
    "DoubleUp": 4,
    "FortyFiveDown": 5,
    "SingleDown": 6,
    "DoubleDown": 7,
}


class DexcomGlucose:
    # Class for storing latest glucose value, trend and time of measurement

    def __init__(self, mgdl: int | None, trend: str, local_time: datetime, utc_time: datetime):
        self.mgdl: int | None = mgdl
        self.mmol: int | None = mgdl_to_mmol(mgdl)
        self.trend: str = trend
        self.trend_numeric = TRENDS[self.trend]
        self.local_time = local_time
        self.utc_time = utc_time
        print(self)

    def __repr__(self):
        return f"<GlucoseValue mgdl:{self.mgdl} mmol:{self.mmol} trend:{self.trend} dt:{self.local_time} wt:{self.utc_time}>"

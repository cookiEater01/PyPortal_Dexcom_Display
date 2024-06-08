from adafruit_datetime import datetime

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

    def __init__(self, display: DisplayMode, mgdl: int | None, mmol: float | None, trend: str = "NotComputable", datetime: datetime = None, time: str = "", invalid: bool = True):
        self.display: DisplayMode = display
        self.mgdl: int | None = mgdl
        self.mmol: float | None = mmol
        self.trend: str = trend
        self.trend_numeric = TRENDS[self.trend]
        self.datetime: datetime | None = datetime
        self.time = time
        self.invalid = invalid
        print(self)
        if self.invalid:
            self.display.add_warning()
        else:
            self.display.remove_warning()
        self.display.update_glucose(self)

    def __repr__(self):
        return f"<GlucoseValue mgdl:{self.mgdl} mmol:{self.mmol} trend:{self.trend} dt:{self.datetime} time:{self.time} invalid:{self.invalid}>"


    def update_values(self, mgdl: int | None, mmol: float | None, trend: str, datetime: datetime, time: str, invalid: bool):
        self.mgdl = mgdl
        self.mmol = mmol
        self.trend = trend
        self.trend_numeric = TRENDS[self.trend]
        self.datetime = datetime
        self.time = time
        self.invalid = invalid
        print(self)
        if self.invalid:
            self.display.add_warning()
        else:
            self.display.remove_warning()
        self.display.update_glucose(self)

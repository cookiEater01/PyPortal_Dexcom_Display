from adafruit_datetime import datetime

# http://www.bcchildrens.ca/endocrinology-diabetes-site/documents/glucoseunits.pdf
def mgdl_to_mmol(mgdl: int):
    if mgdl is None:
        return None
    return round(mgdl / 18.0182, 1)


def get_dt_from_epoch(rsp: str):
    correct_rsp = rsp.strip("\)").replace("Date(", "")

    dt = datetime.fromtimestamp(int(correct_rsp) / 1000.0)
    dt_iso = dt.isoformat()

    return dt_iso

# Backlight function
# Value between 0 and 1 where 0 is OFF, 0.5 is 50% and 1 is 100% brightness.
def set_backlight(val: float, display):
    val = max(0, min(1.0, val))
    display.brightness = val

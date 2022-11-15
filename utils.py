from adafruit_datetime import datetime

# http://www.bcchildrens.ca/endocrinology-diabetes-site/documents/glucoseunits.pdf
def mgdl_to_mmol(mgdl: int):
    return round(mgdl / 18.0182, 1)


def get_dt_from_epoch(rsp: str):
    correct_rsp = rsp.strip("\)").replace("Date(", "")

    dt = datetime.fromtimestamp(int(correct_rsp) / 1000.0)
    dt_iso = dt.isoformat()

    return dt_iso

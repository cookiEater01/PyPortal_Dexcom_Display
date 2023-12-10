from adafruit_datetime import datetime, timedelta


# http://www.bcchildrens.ca/endocrinology-diabetes-site/documents/glucoseunits.pdf
def mgdl_to_mmol(mgdl: int | None):
    if mgdl is None:
        return None
    return round(mgdl / 18.0182, 1)


def parse_date(input_str: str) -> datetime:
    # Remove 'Date(' and ')' from the input string
    input_str = input_str.replace('Date(', '').replace(')', '')

    # Split the input string into timestamp and offset (if present)
    parts = input_str.split('+')

    # Extract timestamp from the first part
    timestamp_str = parts[0][:-3]
    timestamp = int(timestamp_str)

    # Initialize offset to 0
    offset = timedelta()

    # If there is an offset part, parse it and update the offset
    if len(parts) == 2:
        offset_str = parts[1]
        offset_hours = int(offset_str[:2])
        offset_minutes = int(offset_str[2:])
        offset = timedelta(hours=offset_hours, minutes=offset_minutes)

    # Convert milliseconds to seconds and create a datetime object
    dt = datetime.fromtimestamp(timestamp)

    # Add the offset to the datetime object
    dt_with_offset = dt + offset

    return dt_with_offset

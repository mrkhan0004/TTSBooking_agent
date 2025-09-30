from datetime import datetime, timedelta
from typing import Optional
import uuid


def generate_ics_content(time_str: str, title: str = "Appointment", date_str: Optional[str] = None) -> str:
    # Create a simple event for given date at given time, 30 minutes long by default
    if date_str:
        y, m, d = [int(x) for x in date_str.split("-")]
        base_date = datetime(y, m, d).date()
    else:
        base_date = datetime.now().date()
    hour, minute = [int(x) for x in time_str.split(":")]
    start_dt = datetime(base_date.year, base_date.month, base_date.day, hour, minute)
    end_dt = start_dt + timedelta(minutes=30)
    uid = str(uuid.uuid4())

    def fmt(dt: datetime) -> str:
        return dt.strftime("%Y%m%dT%H%M%S")

    ics = """
BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//LocalAgent//Booking//EN
BEGIN:VEVENT
UID:{uid}
DTSTAMP:{dtstamp}Z
DTSTART:{dtstart}Z
DTEND:{dtend}Z
SUMMARY:{title}
END:VEVENT
END:VCALENDAR
""".strip().format(
        uid=uid,
        dtstamp=fmt(datetime.utcnow()),
        dtstart=fmt(start_dt),
        dtend=fmt(end_dt),
        title=title,
    )
    return ics




from datetime import datetime


def parse_email_date_format(date: str):
    return str(datetime.strptime(date, "%a, %d %b %Y %H:%M:%S %z"))
